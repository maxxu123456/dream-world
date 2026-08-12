use std::io;
use std::net::{Ipv4Addr, SocketAddr, TcpStream};
use std::path::PathBuf;
use std::process::{Command, Output};
use std::time::Duration;

pub const IMAGE: &str = "ghcr.io/maxxu123456/dream-world:latest";
pub const CONTAINER_NAME: &str = "dream-world-gui";
pub const VOLUME_NAME: &str = "dream-world-data";

const MANAGED_LABEL: &str = "io.github.maxxu123456.dream-world.gui";
const HOST_IP_LABEL: &str = "io.github.maxxu123456.dream-world.host-ip";

#[derive(Debug, Clone, Default)]
pub struct Snapshot {
    pub docker: DockerState,
    pub container: ContainerState,
    pub site_ready: bool,
}

#[derive(Debug, Clone, Default)]
pub enum DockerState {
    #[default]
    Checking,
    NotInstalled,
    NotRunning(String),
    Ready(String),
}

#[derive(Debug, Clone, Default)]
pub enum ContainerState {
    #[default]
    Unknown,
    NotCreated,
    Running(HealthState),
    Stopped(String),
    Foreign(String),
    Error(String),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HealthState {
    Healthy,
    Starting,
    Unhealthy,
    None,
    Other(String),
}

impl ContainerState {
    pub fn is_running(&self) -> bool {
        matches!(self, Self::Running(_))
    }

    pub fn is_managed(&self) -> bool {
        matches!(self, Self::Running(_) | Self::Stopped(_))
    }
}

pub fn inspect() -> Snapshot {
    let version = match docker_output(&["version", "--format", "{{.Server.Version}}"]) {
        Err(error) if error.kind() == io::ErrorKind::NotFound => {
            return Snapshot {
                docker: DockerState::NotInstalled,
                container: ContainerState::Unknown,
                site_ready: false,
            };
        }
        Err(error) => {
            return Snapshot {
                docker: DockerState::NotRunning(format!("Could not run Docker: {error}")),
                container: ContainerState::Unknown,
                site_ready: false,
            };
        }
        Ok(output) if !output.status.success() => {
            return Snapshot {
                docker: DockerState::NotRunning(readable_failure(&output)),
                container: ContainerState::Unknown,
                site_ready: false,
            };
        }
        Ok(output) => String::from_utf8_lossy(&output.stdout).trim().to_owned(),
    };

    let format = format!(
        "{{{{.State.Status}}}}|{{{{if .State.Health}}}}{{{{.State.Health.Status}}}}{{{{else}}}}none{{{{end}}}}|{{{{index .Config.Labels \"{MANAGED_LABEL}\"}}}}"
    );

    let container =
        match docker_output(&["container", "inspect", "--format", &format, CONTAINER_NAME]) {
            Err(error) => {
                ContainerState::Error(format!("Could not inspect the container: {error}"))
            }
            Ok(output) if output.status.success() => {
                parse_container_state(String::from_utf8_lossy(&output.stdout).trim())
            }
            Ok(output) if is_missing_container(&output) => ContainerState::NotCreated,
            Ok(output) => ContainerState::Error(readable_failure(&output)),
        };

    let site_ready = container.is_running()
        && TcpStream::connect_timeout(
            &SocketAddr::new(Ipv4Addr::LOCALHOST.into(), 8080),
            Duration::from_millis(250),
        )
        .is_ok();

    Snapshot {
        docker: DockerState::Ready(version),
        container,
        site_ready,
    }
}

pub fn start(host_ip: &str) -> Result<String, String> {
    ensure_docker_running()?;
    ensure_container_is_safe_to_replace()?;
    run_checked(&["volume", "create", VOLUME_NAME])?;

    if managed_container_exists()? {
        // Give PID 1 time to forward the signal and reap both servers before
        // replacing the container with the selected IP/latest local image.
        run_checked(&["container", "stop", "--time", "20", CONTAINER_NAME])?;
        run_checked(&["container", "rm", "--force", CONTAINER_NAME])?;
    }

    let host_label = format!("{HOST_IP_LABEL}={host_ip}");
    let host_env = format!("HOST_IP={host_ip}");
    let volume = format!("{VOLUME_NAME}:/opt/server/save_data");
    let dns = format!("{host_ip}:53:53/udp");
    let http = format!("{host_ip}:80:80/tcp");
    let https = format!("{host_ip}:443:443/tcp");
    let gamespy = format!("{host_ip}:29900:29900/tcp");

    run_checked(&[
        "run",
        "--detach",
        "--name",
        CONTAINER_NAME,
        "--restart",
        "unless-stopped",
        "--label",
        &format!("{MANAGED_LABEL}=true"),
        "--label",
        &host_label,
        "--env",
        &host_env,
        "--volume",
        &volume,
        "--publish",
        &dns,
        "--publish",
        &http,
        "--publish",
        &https,
        "--publish",
        &gamespy,
        "--publish",
        "127.0.0.1:8080:8080/tcp",
        IMAGE,
    ])?;

    Ok(format!(
        "Dream World started. Set the DS Primary DNS to {host_ip}, then perform the first tuck-in."
    ))
}

pub fn stop() -> Result<String, String> {
    ensure_docker_running()?;

    match container_ownership()? {
        Ownership::Missing => Ok("Dream World is already stopped.".to_owned()),
        Ownership::Foreign => Err(foreign_container_error()),
        Ownership::Managed => {
            run_checked(&["container", "stop", "--time", "20", CONTAINER_NAME])?;
            Ok("Dream World stopped. Your saved data is still in dream-world-data.".to_owned())
        }
    }
}

pub fn pull_image() -> Result<String, String> {
    ensure_docker_running()?;
    run_checked(&["pull", IMAGE])?;
    Ok("The latest image was downloaded. Restart Dream World to use it.".to_owned())
}

pub fn logs() -> Result<String, String> {
    match container_ownership() {
        Ok(Ownership::Missing) => return Ok(String::new()),
        Ok(Ownership::Foreign) => {
            return Ok(format!(
                "Logs are hidden because the '{CONTAINER_NAME}' container was not created by this app."
            ));
        }
        Ok(Ownership::Managed) => {}
        Err(error) => return Err(error),
    }

    let output = match docker_output(&[
        "container",
        "logs",
        "--timestamps",
        "--tail",
        "400",
        CONTAINER_NAME,
    ]) {
        Err(error) if error.kind() == io::ErrorKind::NotFound => return Ok(String::new()),
        Err(error) => return Err(format!("Could not read Docker logs: {error}")),
        Ok(output) if output.status.success() => output,
        Ok(output) if is_missing_container(&output) => return Ok(String::new()),
        Ok(output) => return Err(readable_failure(&output)),
    };

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    let mut lines: Vec<&str> = stdout.lines().chain(stderr.lines()).collect();
    lines.sort_unstable();

    let logs = lines.join("\n");
    let minimum = logs.len().saturating_sub(200_000);
    let boundary = logs
        .char_indices()
        .find_map(|(index, _)| (index >= minimum).then_some(index))
        .unwrap_or(0);

    Ok(logs[boundary..].to_owned())
}

fn parse_container_state(value: &str) -> ContainerState {
    let mut fields = value.splitn(3, '|');
    let status = fields.next().unwrap_or("unknown");
    let health = fields.next().unwrap_or("none");
    let managed = fields.next().unwrap_or_default();

    if managed != "true" {
        return ContainerState::Foreign(status.to_owned());
    }

    if status == "running" {
        let health = match health {
            "healthy" => HealthState::Healthy,
            "starting" => HealthState::Starting,
            "unhealthy" => HealthState::Unhealthy,
            "none" | "<no value>" | "" => HealthState::None,
            other => HealthState::Other(other.to_owned()),
        };
        ContainerState::Running(health)
    } else {
        ContainerState::Stopped(status.to_owned())
    }
}

fn ensure_docker_running() -> Result<(), String> {
    let output =
        docker_output(&["version", "--format", "{{.Server.Version}}"]).map_err(|error| {
            if error.kind() == io::ErrorKind::NotFound {
                "Docker is not installed. Install and open Docker Desktop first.".to_owned()
            } else {
                format!("Could not run Docker: {error}")
            }
        })?;

    if output.status.success() {
        Ok(())
    } else {
        Err(format!(
            "Docker is installed but is not running. Open Docker Desktop and wait for it to finish starting. {}",
            readable_failure(&output)
        ))
    }
}

fn ensure_container_is_safe_to_replace() -> Result<(), String> {
    if matches!(container_ownership()?, Ownership::Foreign) {
        Err(foreign_container_error())
    } else {
        Ok(())
    }
}

fn managed_container_exists() -> Result<bool, String> {
    Ok(matches!(container_ownership()?, Ownership::Managed))
}

fn container_ownership() -> Result<Ownership, String> {
    let format = format!("{{{{index .Config.Labels \"{MANAGED_LABEL}\"}}}}");
    let output = docker_output(&["container", "inspect", "--format", &format, CONTAINER_NAME])
        .map_err(|error| format!("Could not inspect the existing container: {error}"))?;

    if output.status.success() {
        if String::from_utf8_lossy(&output.stdout).trim() == "true" {
            Ok(Ownership::Managed)
        } else {
            Ok(Ownership::Foreign)
        }
    } else if is_missing_container(&output) {
        Ok(Ownership::Missing)
    } else {
        Err(readable_failure(&output))
    }
}

fn foreign_container_error() -> String {
    format!(
        "A container named {CONTAINER_NAME} already exists but was not created by this app. Rename or remove it in Docker Desktop, then try again. It was left untouched."
    )
}

fn run_checked(args: &[&str]) -> Result<String, String> {
    let output = docker_output(args).map_err(|error| {
        if error.kind() == io::ErrorKind::NotFound {
            "Docker is not installed. Install and open Docker Desktop first.".to_owned()
        } else {
            format!("Could not run Docker: {error}")
        }
    })?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).trim().to_owned())
    } else {
        Err(readable_failure(&output))
    }
}

fn docker_output(args: &[&str]) -> io::Result<Output> {
    Command::new(docker_executable()).args(args).output()
}

fn docker_executable() -> PathBuf {
    if executable_on_path("docker") {
        return PathBuf::from("docker");
    }

    platform_docker_candidates()
        .into_iter()
        .find(|path| path.is_file())
        .unwrap_or_else(|| PathBuf::from("docker"))
}

fn executable_on_path(name: &str) -> bool {
    let Some(path) = std::env::var_os("PATH") else {
        return false;
    };

    std::env::split_paths(&path).any(|directory| {
        let candidate = directory.join(name);
        if candidate.is_file() {
            return true;
        }

        #[cfg(target_os = "windows")]
        if directory.join(format!("{name}.exe")).is_file() {
            return true;
        }

        false
    })
}

fn platform_docker_candidates() -> Vec<PathBuf> {
    let mut candidates = Vec::new();

    #[cfg(target_os = "macos")]
    {
        if let Some(home) = std::env::var_os("HOME") {
            candidates.push(PathBuf::from(home).join(".docker/bin/docker"));
        }
        candidates.extend([
            PathBuf::from("/usr/local/bin/docker"),
            PathBuf::from("/opt/homebrew/bin/docker"),
            PathBuf::from("/Applications/Docker.app/Contents/Resources/bin/docker"),
        ]);
    }

    #[cfg(all(unix, not(target_os = "macos")))]
    candidates.extend([
        PathBuf::from("/usr/bin/docker"),
        PathBuf::from("/usr/local/bin/docker"),
        PathBuf::from("/snap/bin/docker"),
    ]);

    #[cfg(target_os = "windows")]
    if let Some(program_files) = std::env::var_os("ProgramFiles") {
        candidates
            .push(PathBuf::from(program_files).join("Docker/Docker/resources/bin/docker.exe"));
    }

    candidates
}

fn readable_failure(output: &Output) -> String {
    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_owned();
    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_owned();

    if !stderr.is_empty() {
        stderr
    } else if !stdout.is_empty() {
        stdout
    } else {
        format!("Docker exited with status {}.", output.status)
    }
}

fn is_missing_container(output: &Output) -> bool {
    let stderr = String::from_utf8_lossy(&output.stderr).to_ascii_lowercase();
    stderr.contains("no such container") || stderr.contains("no such object")
}

#[derive(Debug, Clone, Copy)]
enum Ownership {
    Missing,
    Managed,
    Foreign,
}

#[cfg(test)]
mod tests {
    use super::{parse_container_state, ContainerState, HealthState};

    #[test]
    fn parses_managed_running_health() {
        assert!(matches!(
            parse_container_state("running|healthy|true"),
            ContainerState::Running(HealthState::Healthy)
        ));
        assert!(matches!(
            parse_container_state("running|starting|true"),
            ContainerState::Running(HealthState::Starting)
        ));
    }

    #[test]
    fn refuses_unlabeled_container() {
        assert!(matches!(
            parse_container_state("running|healthy|<no value>"),
            ContainerState::Foreign(status) if status == "running"
        ));
    }
}

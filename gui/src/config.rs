use std::env;
use std::fs;
use std::path::PathBuf;

const APP_DIRECTORY: &str = "dream-world-gui";
const HOST_IP_FILE: &str = "host-ip";
const FRIEND_CODE_FILE: &str = "friend-code";
const FRIEND_CODE_MODE_FILE: &str = "use-existing-friend-code";

pub fn load_host_ip() -> Result<Option<String>, String> {
    load_setting(HOST_IP_FILE, "DNS IP")
}

pub fn load_friend_code() -> Result<Option<String>, String> {
    load_setting(FRIEND_CODE_FILE, "Friend Code")
}

pub fn load_friend_code_mode() -> Result<Option<bool>, String> {
    match load_setting(FRIEND_CODE_MODE_FILE, "Friend Code mode")? {
        Some(value) if value == "true" => Ok(Some(true)),
        Some(value) if value == "false" => Ok(Some(false)),
        Some(_) => Err("The saved Friend Code mode was invalid and was ignored.".to_owned()),
        None => Ok(None),
    }
}

fn load_setting(file_name: &str, label: &str) -> Result<Option<String>, String> {
    let path = settings_directory()?.join(file_name);

    match fs::read_to_string(&path) {
        Ok(contents) => {
            let value = contents.trim();
            Ok((!value.is_empty()).then(|| value.to_owned()))
        }
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(None),
        Err(error) => Err(format!(
            "Could not read the saved {label} at {}: {error}",
            path.display()
        )),
    }
}

pub fn save_host_ip(host_ip: &str) -> Result<(), String> {
    save_setting(HOST_IP_FILE, "DNS IP", host_ip)
}

pub fn save_friend_code(friend_code: &str) -> Result<(), String> {
    save_setting(FRIEND_CODE_FILE, "Friend Code", friend_code)
}

pub fn save_friend_code_mode(use_existing: bool) -> Result<(), String> {
    save_setting(
        FRIEND_CODE_MODE_FILE,
        "Friend Code mode",
        if use_existing { "true" } else { "false" },
    )
}

fn save_setting(file_name: &str, label: &str, value: &str) -> Result<(), String> {
    let parent = settings_directory()?;
    let path = parent.join(file_name);

    fs::create_dir_all(&parent).map_err(|error| {
        format!(
            "Could not create the settings directory {}: {error}",
            parent.display()
        )
    })?;

    fs::write(&path, format!("{value}\n"))
        .map_err(|error| format!("Could not save the {label} at {}: {error}", path.display()))
}

fn settings_directory() -> Result<PathBuf, String> {
    #[cfg(target_os = "windows")]
    {
        return env::var_os("APPDATA")
            .map(PathBuf::from)
            .map(|path| path.join(APP_DIRECTORY))
            .ok_or_else(|| "Windows did not provide an APPDATA directory.".to_owned());
    }

    #[cfg(target_os = "macos")]
    {
        return env::var_os("HOME")
            .map(PathBuf::from)
            .map(|path| {
                path.join("Library")
                    .join("Application Support")
                    .join(APP_DIRECTORY)
            })
            .ok_or_else(|| "macOS did not provide a HOME directory.".to_owned());
    }

    #[cfg(all(unix, not(target_os = "macos")))]
    {
        if let Some(path) = env::var_os("XDG_CONFIG_HOME") {
            return Ok(PathBuf::from(path).join(APP_DIRECTORY));
        }

        return env::var_os("HOME")
            .map(PathBuf::from)
            .map(|path| path.join(".config").join(APP_DIRECTORY))
            .ok_or_else(|| {
                "Linux did not provide XDG_CONFIG_HOME or a HOME directory.".to_owned()
            });
    }

    #[allow(unreachable_code)]
    Err("This platform does not have a supported settings directory.".to_owned())
}

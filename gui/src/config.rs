use std::env;
use std::fs;
use std::path::PathBuf;

const APP_DIRECTORY: &str = "dream-world-gui";
const CONFIG_FILE: &str = "host-ip";

pub fn load_host_ip() -> Result<Option<String>, String> {
    let path = config_path()?;

    match fs::read_to_string(&path) {
        Ok(contents) => {
            let value = contents.trim();
            Ok((!value.is_empty()).then(|| value.to_owned()))
        }
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(None),
        Err(error) => Err(format!(
            "Could not read the saved DNS IP at {}: {error}",
            path.display()
        )),
    }
}

pub fn save_host_ip(host_ip: &str) -> Result<(), String> {
    let path = config_path()?;
    let parent = path
        .parent()
        .ok_or_else(|| "Could not determine the settings directory.".to_owned())?;

    fs::create_dir_all(parent).map_err(|error| {
        format!(
            "Could not create the settings directory {}: {error}",
            parent.display()
        )
    })?;

    fs::write(&path, format!("{host_ip}\n"))
        .map_err(|error| format!("Could not save the DNS IP at {}: {error}", path.display()))
}

fn config_path() -> Result<PathBuf, String> {
    #[cfg(target_os = "windows")]
    {
        return env::var_os("APPDATA")
            .map(PathBuf::from)
            .map(|path| path.join(APP_DIRECTORY).join(CONFIG_FILE))
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
                    .join(CONFIG_FILE)
            })
            .ok_or_else(|| "macOS did not provide a HOME directory.".to_owned());
    }

    #[cfg(all(unix, not(target_os = "macos")))]
    {
        if let Some(path) = env::var_os("XDG_CONFIG_HOME") {
            return Ok(PathBuf::from(path).join(APP_DIRECTORY).join(CONFIG_FILE));
        }

        return env::var_os("HOME")
            .map(PathBuf::from)
            .map(|path| path.join(".config").join(APP_DIRECTORY).join(CONFIG_FILE))
            .ok_or_else(|| {
                "Linux did not provide XDG_CONFIG_HOME or a HOME directory.".to_owned()
            });
    }

    #[allow(unreachable_code)]
    Err("This platform does not have a supported settings directory.".to_owned())
}

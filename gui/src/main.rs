#![cfg_attr(target_os = "windows", windows_subsystem = "windows")]

mod config;
mod docker;
mod friend_code;
mod network;

use docker::{ContainerState, DockerState, HealthState, Snapshot};
use iced::widget::{button, column, container, row, scrollable, text, text_input, Space};
use iced::{Alignment, Color, Element, Fill, Font, Length, Subscription, Task, Theme};
use std::process::Command;
use std::time::Duration;

const DOCKER_INSTALL_URL: &str = "https://www.docker.com/products/docker-desktop/";
const DREAM_WORLD_URL: &str = "http://127.0.0.1:8080/";
const PLAYER_UPLOAD_MILESTONE: &str = "Player upload found; Dream World site is starting";

fn main() -> iced::Result {
    iced::application("Dream World", App::update, App::view)
        .subscription(App::subscription)
        .theme(|_| Theme::Light)
        .window_size((1080.0, 780.0))
        .centered()
        .antialiasing(true)
        .run_with(App::new)
}

struct App {
    host_ip: String,
    confirmed_host_ip: Option<String>,
    friend_code: String,
    confirmed_friend_code: Option<String>,
    detected_host_ip: Option<String>,
    detection_error: Option<String>,
    ip_error: Option<String>,
    friend_code_error: Option<String>,
    snapshot: Snapshot,
    logs: String,
    logs_error: Option<String>,
    feedback: Feedback,
    operation: Option<Action>,
    poll_in_flight: bool,
    logs_in_flight: bool,
    logs_id: scrollable::Id,
}

#[derive(Debug, Clone)]
enum Message {
    Tick,
    HostIpChanged(String),
    UseDetectedIp,
    SaveHostIp,
    FriendCodeChanged(String),
    SaveFriendCode,
    Start,
    Stop,
    Restart,
    Pull,
    DockerPolled(Snapshot),
    LogsLoaded(Result<String, String>),
    ActionFinished(Result<String, String>),
    OpenDreamWorld,
    OpenDockerInstall,
    UrlOpened(Result<String, String>),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Action {
    Start,
    Stop,
    Restart,
    Pull,
}

impl Action {
    fn progress_message(self) -> &'static str {
        match self {
            Self::Start => "Starting Dream World. The image will download first if needed...",
            Self::Stop => "Stopping Dream World safely...",
            Self::Restart => {
                "Restarting with the saved DNS IP, Friend Code, and latest downloaded image..."
            }
            Self::Pull => "Pulling the latest image. This can take a few minutes...",
        }
    }
}

#[derive(Debug, Clone)]
struct Feedback {
    message: String,
    is_error: bool,
}

impl Feedback {
    fn info(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
            is_error: false,
        }
    }

    fn error(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
            is_error: true,
        }
    }
}

impl App {
    fn new() -> (Self, Task<Message>) {
        let (detected_host_ip, detection_error) = match network::detect_lan_ipv4() {
            Ok(ip) => (Some(ip.to_string()), None),
            Err(error) => (None, Some(error)),
        };

        let (saved_host_ip, settings_error) = match config::load_host_ip() {
            Ok(Some(value)) if network::validate_host_ip(&value).is_ok() => (Some(value), None),
            Ok(Some(_)) => (
                None,
                Some("The previously saved DNS IP was invalid and was ignored.".to_owned()),
            ),
            Ok(None) => (None, None),
            Err(error) => (None, Some(error)),
        };

        let host_ip = saved_host_ip
            .clone()
            .or_else(|| detected_host_ip.clone())
            .unwrap_or_default();

        let (saved_friend_code, friend_code_settings_error) = match config::load_friend_code() {
            Ok(Some(value)) => match friend_code::validate(&value) {
                Ok(code) => (Some(code.normalized), None),
                Err(_) => (
                    None,
                    Some(
                        "The previously saved Friend Code was invalid and was ignored.".to_owned(),
                    ),
                ),
            },
            Ok(None) => (None, None),
            Err(error) => (None, Some(error)),
        };

        let friend_code = saved_friend_code.clone().unwrap_or_default();

        let feedback = if let Some(error) = settings_error.or(friend_code_settings_error) {
            Feedback::error(error)
        } else if saved_host_ip.is_some() && saved_friend_code.is_some() {
            Feedback::info("Saved setup loaded. Docker status is being checked...")
        } else if saved_host_ip.is_some() {
            Feedback::info("DNS IP loaded. Enter the Friend Code from your game's Pal Pad.")
        } else if detected_host_ip.is_some() {
            Feedback::info(
                "LAN IP detected. Confirm it is the address shared with your DS, then save it.",
            )
        } else {
            Feedback::info("Enter this computer's LAN IPv4 address to begin.")
        };

        (
            Self {
                host_ip,
                confirmed_host_ip: saved_host_ip,
                friend_code,
                confirmed_friend_code: saved_friend_code,
                detected_host_ip,
                detection_error,
                ip_error: None,
                friend_code_error: None,
                snapshot: Snapshot::default(),
                logs: String::new(),
                logs_error: None,
                feedback,
                operation: None,
                poll_in_flight: true,
                logs_in_flight: true,
                logs_id: scrollable::Id::new("docker-logs"),
            },
            Task::batch([Self::poll_task(), Self::logs_task()]),
        )
    }

    fn subscription(&self) -> Subscription<Message> {
        iced::time::every(Duration::from_secs(2)).map(|_| Message::Tick)
    }

    fn update(&mut self, message: Message) -> Task<Message> {
        match message {
            Message::Tick => {
                let mut tasks = Vec::new();

                if !self.poll_in_flight {
                    self.poll_in_flight = true;
                    tasks.push(Self::poll_task());
                }

                if !self.logs_in_flight && matches!(self.snapshot.docker, DockerState::Ready(_)) {
                    self.logs_in_flight = true;
                    tasks.push(Self::logs_task());
                }

                Task::batch(tasks)
            }
            Message::HostIpChanged(value) => {
                self.host_ip = value;
                self.ip_error = None;
                Task::none()
            }
            Message::UseDetectedIp => {
                if let Some(host_ip) = &self.detected_host_ip {
                    self.host_ip.clone_from(host_ip);
                    self.ip_error = None;
                    self.feedback = Feedback::info(
                        "Detected address selected. Save it after confirming the DS uses the same network.",
                    );
                }
                Task::none()
            }
            Message::SaveHostIp => {
                let host_ip = match network::validate_host_ip(&self.host_ip) {
                    Ok(ip) => ip.to_string(),
                    Err(error) => {
                        self.ip_error = Some(error.clone());
                        self.feedback = Feedback::error(error);
                        return Task::none();
                    }
                };

                match config::save_host_ip(&host_ip) {
                    Ok(()) => {
                        self.host_ip.clone_from(&host_ip);
                        self.confirmed_host_ip = Some(host_ip.clone());
                        self.ip_error = None;
                        self.feedback = Feedback::info(format!(
                            "DNS IP {host_ip} saved. Use this same address as the DS Primary DNS."
                        ));
                    }
                    Err(error) => self.feedback = Feedback::error(error),
                }

                Task::none()
            }
            Message::FriendCodeChanged(value) => {
                self.friend_code = value;
                self.friend_code_error = None;
                Task::none()
            }
            Message::SaveFriendCode => {
                let friend_code = match friend_code::validate(&self.friend_code) {
                    Ok(code) => code.normalized,
                    Err(error) => {
                        self.friend_code_error = Some(error.clone());
                        self.feedback = Feedback::error(error);
                        return Task::none();
                    }
                };

                match config::save_friend_code(&friend_code) {
                    Ok(()) => {
                        self.friend_code.clone_from(&friend_code);
                        self.confirmed_friend_code = Some(friend_code);
                        self.friend_code_error = None;
                        self.feedback = Feedback::info(
                            "Friend Code saved. It will prevent the profile mismatch that causes error 60000.",
                        );
                    }
                    Err(error) => self.feedback = Feedback::error(error),
                }

                Task::none()
            }
            Message::Start => self.begin_action(Action::Start),
            Message::Stop => self.begin_action(Action::Stop),
            Message::Restart => self.begin_action(Action::Restart),
            Message::Pull => self.begin_action(Action::Pull),
            Message::DockerPolled(snapshot) => {
                self.poll_in_flight = false;
                self.snapshot = snapshot;
                Task::none()
            }
            Message::LogsLoaded(result) => {
                self.logs_in_flight = false;

                match result {
                    Ok(logs) => {
                        self.logs_error = None;
                        if logs != self.logs {
                            self.logs = logs;
                            return scrollable::snap_to(
                                self.logs_id.clone(),
                                scrollable::RelativeOffset::END,
                            );
                        }
                    }
                    Err(error) => self.logs_error = Some(error),
                }

                Task::none()
            }
            Message::ActionFinished(result) => {
                self.operation = None;
                self.feedback = match result {
                    Ok(message) => Feedback::info(message),
                    Err(error) => Feedback::error(error),
                };

                let mut tasks = Vec::new();
                if !self.poll_in_flight {
                    self.poll_in_flight = true;
                    tasks.push(Self::poll_task());
                }
                if !self.logs_in_flight {
                    self.logs_in_flight = true;
                    tasks.push(Self::logs_task());
                }

                Task::batch(tasks)
            }
            Message::OpenDreamWorld => {
                self.feedback = Feedback::info("Opening Dream World in your default browser...");
                Self::open_url_task(DREAM_WORLD_URL)
            }
            Message::OpenDockerInstall => {
                self.feedback = Feedback::info("Opening the Docker Desktop download page...");
                Self::open_url_task(DOCKER_INSTALL_URL)
            }
            Message::UrlOpened(result) => {
                self.feedback = match result {
                    Ok(message) => Feedback::info(message),
                    Err(error) => Feedback::error(error),
                };
                Task::none()
            }
        }
    }

    fn begin_action(&mut self, action: Action) -> Task<Message> {
        if self.operation.is_some() {
            return Task::none();
        }

        if matches!(action, Action::Start | Action::Restart) && self.ready_host_ip().is_none() {
            let error = "Confirm and save a valid DNS IP before starting Dream World.";
            self.feedback = Feedback::error(error);
            self.ip_error = Some(error.to_owned());
            return Task::none();
        }

        if matches!(action, Action::Start | Action::Restart) && self.ready_friend_code().is_none() {
            let error = "Enter and save the 12-digit Friend Code from your Pal Pad before starting Dream World.";
            self.feedback = Feedback::error(error);
            self.friend_code_error = Some(error.to_owned());
            return Task::none();
        }

        let host_ip = self.ready_host_ip().unwrap_or_default();
        let friend_code = self.ready_friend_code().unwrap_or_default();
        self.operation = Some(action);
        self.feedback = Feedback::info(action.progress_message());

        Task::perform(
            async move {
                match action {
                    Action::Start | Action::Restart => docker::start(&host_ip, &friend_code),
                    Action::Stop => docker::stop(),
                    Action::Pull => docker::pull_image(),
                }
            },
            Message::ActionFinished,
        )
    }

    fn ready_host_ip(&self) -> Option<String> {
        let valid = network::validate_host_ip(&self.host_ip).ok()?.to_string();
        (self.confirmed_host_ip.as_deref() == Some(valid.as_str())).then_some(valid)
    }

    fn ready_friend_code(&self) -> Option<String> {
        let valid = friend_code::validate(&self.friend_code).ok()?.normalized;
        (self.confirmed_friend_code.as_deref() == Some(valid.as_str())).then_some(valid)
    }

    fn poll_task() -> Task<Message> {
        Task::perform(async { docker::inspect() }, Message::DockerPolled)
    }

    fn logs_task() -> Task<Message> {
        Task::perform(async { docker::logs() }, Message::LogsLoaded)
    }

    fn open_url_task(url: &'static str) -> Task<Message> {
        Task::perform(async move { open_url(url) }, Message::UrlOpened)
    }

    fn view(&self) -> Element<'_, Message> {
        let header = column![
            text("Dream World").size(34),
            text("Run the complete service for your DS without using a terminal.")
                .size(16)
                .color(Color::from_rgb8(78, 92, 110)),
        ]
        .spacing(4);

        let body = row![self.controls_panel(), self.logs_panel()]
            .spacing(18)
            .height(Fill);

        container(column![header, body].spacing(18).height(Fill))
            .padding(24)
            .width(Fill)
            .height(Fill)
            .into()
    }

    fn controls_panel(&self) -> Element<'_, Message> {
        let docker_card = self.docker_card();
        let ip_card = self.ip_card();
        let friend_code_card = self.friend_code_card();
        let action_card = self.action_card();
        let instructions = self.instructions_card();

        let feedback_color = if self.feedback.is_error {
            Color::from_rgb8(180, 42, 42)
        } else {
            Color::from_rgb8(42, 93, 68)
        };

        let content = column![
            docker_card,
            ip_card,
            friend_code_card,
            action_card,
            container(text(&self.feedback.message).size(14).color(feedback_color))
                .padding(12)
                .width(Fill)
                .style(container::rounded_box),
            instructions,
        ]
        .spacing(12)
        .width(Length::Fixed(400.0));

        scrollable(content)
            .width(Length::Fixed(416.0))
            .height(Fill)
            .into()
    }

    fn docker_card(&self) -> Element<'_, Message> {
        let (headline, detail, color) = self.status_copy();
        let mut content = column![
            text("Docker and server").size(19),
            text(headline).size(17).color(color),
            text(detail).size(13).color(Color::from_rgb8(78, 92, 110)),
        ]
        .spacing(6);

        if matches!(self.snapshot.docker, DockerState::NotInstalled) {
            content = content.push(
                button("Install Docker Desktop")
                    .on_press(Message::OpenDockerInstall)
                    .style(button::secondary),
            );
        }

        container(content)
            .padding(15)
            .width(Fill)
            .style(container::rounded_box)
            .into()
    }

    fn ip_card(&self) -> Element<'_, Message> {
        let saved = self.ready_host_ip().is_some();
        let valid = network::validate_host_ip(&self.host_ip).is_ok();
        let mut save_button =
            button(if saved { "DNS IP saved" } else { "Save DNS IP" }).style(if saved {
                button::success
            } else {
                button::primary
            });

        if valid && !saved && self.operation.is_none() {
            save_button = save_button.on_press(Message::SaveHostIp);
        }

        let mut detected_row = row![].spacing(8).align_y(Alignment::Center);
        if let Some(detected) = &self.detected_host_ip {
            detected_row = detected_row
                .push(text(format!("Detected: {detected}")).size(13))
                .push(
                    button("Use detected")
                        .on_press(Message::UseDetectedIp)
                        .style(button::secondary),
                );
        } else if let Some(error) = &self.detection_error {
            detected_row =
                detected_row.push(text(error).size(12).color(Color::from_rgb8(150, 70, 45)));
        }

        let mut content = column![
            text("DS Primary DNS").size(19),
            text("Confirm this computer's LAN IPv4 on the same network as the DS.")
                .size(13)
                .color(Color::from_rgb8(78, 92, 110)),
            row![
                text_input("192.168.1.50", &self.host_ip)
                    .on_input(Message::HostIpChanged)
                    .on_submit(Message::SaveHostIp)
                    .padding(10)
                    .width(Fill),
                save_button,
            ]
            .spacing(8)
            .align_y(Alignment::Center),
            detected_row,
        ]
        .spacing(9);

        if let Some(error) = &self.ip_error {
            content = content.push(text(error).size(12).color(Color::from_rgb8(180, 42, 42)));
        }

        container(content)
            .padding(15)
            .width(Fill)
            .style(container::rounded_box)
            .into()
    }

    fn friend_code_card(&self) -> Element<'_, Message> {
        let saved = self.ready_friend_code().is_some();
        let valid = friend_code::validate(&self.friend_code).is_ok();
        let mut save_button = button(if saved {
            "Friend Code saved"
        } else {
            "Save Friend Code"
        })
        .style(if saved {
            button::success
        } else {
            button::primary
        });

        if valid && !saved && self.operation.is_none() {
            save_button = save_button.on_press(Message::SaveFriendCode);
        }

        let mut content = column![
            text("In-game Friend Code").size(19),
            text("Required: open the game's Pal Pad and enter its 12-digit Friend Code. This makes the server use the profile ID already stored in this save and prevents error 60000.")
                .size(13)
                .color(Color::from_rgb8(78, 92, 110)),
            row![
                text_input("0000-0000-0000", &self.friend_code)
                    .on_input(Message::FriendCodeChanged)
                    .on_submit(Message::SaveFriendCode)
                    .padding(10)
                    .width(Fill),
                save_button,
            ]
            .spacing(8)
            .align_y(Alignment::Center),
            text("Use the code for the same game and save that will connect to Dream World.")
                .size(12)
                .color(Color::from_rgb8(78, 92, 110)),
        ]
        .spacing(9);

        if let Some(error) = &self.friend_code_error {
            content = content.push(text(error).size(12).color(Color::from_rgb8(180, 42, 42)));
        }

        container(content)
            .padding(15)
            .width(Fill)
            .style(container::rounded_box)
            .into()
    }

    fn action_card(&self) -> Element<'_, Message> {
        let docker_ready = matches!(self.snapshot.docker, DockerState::Ready(_));
        let idle = self.operation.is_none();
        let running = self.snapshot.container.is_running();
        let managed = self.snapshot.container.is_managed();
        let startable = matches!(
            self.snapshot.container,
            ContainerState::NotCreated | ContainerState::Stopped(_)
        );
        let host_ready = self.ready_host_ip().is_some();
        let friend_code_ready = self.ready_friend_code().is_some();

        let mut start = button("Start").style(button::success);
        if docker_ready && idle && host_ready && friend_code_ready && startable {
            start = start.on_press(Message::Start);
        }

        let mut stop = button("Stop").style(button::danger);
        if docker_ready && idle && running {
            stop = stop.on_press(Message::Stop);
        }

        let mut restart = button("Restart").style(button::secondary);
        if docker_ready && idle && host_ready && friend_code_ready && managed {
            restart = restart.on_press(Message::Restart);
        }

        let mut pull = button("Pull / Update image").style(button::primary);
        if docker_ready && idle {
            pull = pull.on_press(Message::Pull);
        }

        let mut open = button("Open Dream World").style(button::primary);
        if self.snapshot.site_ready && idle {
            open = open.on_press(Message::OpenDreamWorld);
        }

        let operation_text = self.operation.map_or(
            "Stop keeps saved data. Restart applies DNS-IP, Friend Code, and image changes.",
            Action::progress_message,
        );

        container(
            column![
                text("Controls").size(19),
                row![start, stop, restart].spacing(8),
                row![pull, open].spacing(8),
                text(operation_text)
                    .size(12)
                    .color(Color::from_rgb8(78, 92, 110)),
            ]
            .spacing(9),
        )
        .padding(15)
        .width(Fill)
        .style(container::rounded_box)
        .into()
    }

    fn instructions_card(&self) -> Element<'_, Message> {
        let ip = self
            .ready_host_ip()
            .unwrap_or_else(|| "your saved LAN IP".to_owned());
        let milestone_seen = self.logs.contains(PLAYER_UPLOAD_MILESTONE);
        let player_ready =
            self.snapshot.container.is_running() && (self.snapshot.site_ready || milestone_seen);

        let readiness = if player_ready {
            "Player upload found — the Dream World website is ready."
        } else {
            "The website intentionally waits for the first player upload."
        };

        container(
            column![
                text("First tuck-in").size(19),
                text(format!("1. Set the DS Primary DNS to {ip}.")).size(13),
                text("2. Open C-Gear, press ONLINE on the bottom screen, then press GAME SYNC and tuck in a Pokémon.").size(13),
                text("3. Keep this app open and watch the live logs. When the player-upload message appears, open Dream World.").size(13),
                text(readiness)
                    .size(13)
                    .color(if player_ready {
                        Color::from_rgb8(28, 125, 78)
                    } else {
                        Color::from_rgb8(78, 92, 110)
                    }),
            ]
            .spacing(6),
        )
        .padding(15)
        .width(Fill)
        .style(container::rounded_box)
        .into()
    }

    fn logs_panel(&self) -> Element<'_, Message> {
        let logs = if self.logs.is_empty() {
            "Live Docker logs will appear here after Start.\n\nOn a new install, Game Sync starts first and remains available while the website waits for the DS's first tuck-in."
        } else {
            &self.logs
        };

        let header = row![
            column![
                text("Live logs").size(21),
                text("Updated every two seconds; newest output is at the bottom.")
                    .size(13)
                    .color(Color::from_rgb8(78, 92, 110)),
            ],
            Space::with_width(Fill),
            text(if self.logs_in_flight {
                "Refreshing..."
            } else {
                "Live"
            })
            .size(13)
            .color(Color::from_rgb8(42, 93, 68)),
        ]
        .align_y(Alignment::Center);

        let log_view = scrollable(
            container(text(logs).font(Font::MONOSPACE).size(13).width(Fill))
                .padding(14)
                .width(Fill),
        )
        .id(self.logs_id.clone())
        .height(Fill);

        let mut content = column![header, log_view].spacing(10).height(Fill);
        if let Some(error) = &self.logs_error {
            content = content.push(text(error).size(12).color(Color::from_rgb8(180, 42, 42)));
        }

        container(content)
            .padding(16)
            .width(Fill)
            .height(Fill)
            .style(container::bordered_box)
            .into()
    }

    fn status_copy(&self) -> (String, String, Color) {
        match (&self.snapshot.docker, &self.snapshot.container) {
            (DockerState::Checking, _) => (
                "Checking Docker...".to_owned(),
                "The app polls Docker automatically.".to_owned(),
                Color::from_rgb8(78, 92, 110),
            ),
            (DockerState::NotInstalled, _) => (
                "Docker is not installed".to_owned(),
                "Install Docker Desktop, open it, then return here. No terminal is required."
                    .to_owned(),
                Color::from_rgb8(180, 42, 42),
            ),
            (DockerState::NotRunning(error), _) => (
                "Docker is installed but not running".to_owned(),
                format!("Open Docker Desktop and wait until it is ready. {error}"),
                Color::from_rgb8(180, 90, 35),
            ),
            (DockerState::Ready(version), ContainerState::Unknown) => (
                "Docker is ready".to_owned(),
                format!("Docker Engine {version}; checking the Dream World container..."),
                Color::from_rgb8(42, 93, 68),
            ),
            (DockerState::Ready(version), ContainerState::NotCreated) => (
                "Stopped — ready to start".to_owned(),
                format!("Docker Engine {version}; no GUI-managed container exists yet."),
                Color::from_rgb8(78, 92, 110),
            ),
            (DockerState::Ready(version), ContainerState::Running(health)) => {
                let (health_label, color) = match health {
                    HealthState::Healthy => ("healthy", Color::from_rgb8(28, 125, 78)),
                    HealthState::Starting => ("health check starting", Color::from_rgb8(180, 90, 35)),
                    HealthState::Unhealthy => ("unhealthy", Color::from_rgb8(180, 42, 42)),
                    HealthState::None => ("running; no health check", Color::from_rgb8(180, 90, 35)),
                    HealthState::Other(value) => (value.as_str(), Color::from_rgb8(180, 90, 35)),
                };
                (
                    format!("Running — {health_label}"),
                    format!(
                        "Docker Engine {version}. Dream World site: {}.",
                        if self.snapshot.site_ready {
                            "ready"
                        } else {
                            "waiting for first tuck-in"
                        }
                    ),
                    color,
                )
            }
            (DockerState::Ready(version), ContainerState::Stopped(status)) => (
                format!("Stopped — {status}"),
                format!("Docker Engine {version}; saved data remains in {}.", docker::VOLUME_NAME),
                Color::from_rgb8(78, 92, 110),
            ),
            (DockerState::Ready(_), ContainerState::Foreign(status)) => (
                "Container name conflict".to_owned(),
                format!(
                    "An unrelated '{}' container is {status}. Rename or remove it in Docker Desktop; this app will not touch it.",
                    docker::CONTAINER_NAME
                ),
                Color::from_rgb8(180, 42, 42),
            ),
            (DockerState::Ready(_), ContainerState::Error(error)) => (
                "Could not inspect Dream World".to_owned(),
                error.clone(),
                Color::from_rgb8(180, 42, 42),
            ),
        }
    }
}

fn open_url(url: &str) -> Result<String, String> {
    #[cfg(target_os = "windows")]
    let status = Command::new("cmd").args(["/C", "start", "", url]).status();

    #[cfg(target_os = "macos")]
    let status = Command::new("open").arg(url).status();

    #[cfg(all(unix, not(target_os = "macos")))]
    let status = Command::new("xdg-open").arg(url).status();

    #[cfg(not(any(target_os = "windows", target_os = "macos", unix)))]
    return Err(format!(
        "Opening links is not supported on this platform. Open {url} manually."
    ));

    match status {
        Ok(code) if code.success() => Ok("Opened in your default browser.".to_owned()),
        Ok(code) => Err(format!(
            "The browser command exited with {code}. Open {url} manually."
        )),
        Err(error) => Err(format!(
            "Could not open the browser: {error}. Open {url} manually."
        )),
    }
}

use std::net::{Ipv4Addr, UdpSocket};

pub fn detect_lan_ipv4() -> Result<Ipv4Addr, String> {
    let socket = UdpSocket::bind((Ipv4Addr::UNSPECIFIED, 0))
        .map_err(|error| format!("Could not inspect this computer's network: {error}"))?;

    // UDP connect selects the interface used by the default route without
    // sending a packet or requiring the remote address to answer.
    socket
        .connect((Ipv4Addr::new(8, 8, 8, 8), 80))
        .map_err(|error| format!("Could not find an active LAN route: {error}"))?;

    match socket.local_addr() {
        Ok(address) => match address.ip() {
            std::net::IpAddr::V4(ip) => {
                validate_host_ip(&ip.to_string())?;
                Ok(ip)
            }
            std::net::IpAddr::V6(_) => {
                Err("The active network route did not have an IPv4 address.".to_owned())
            }
        },
        Err(error) => Err(format!("Could not read the active LAN address: {error}")),
    }
}

pub fn validate_host_ip(value: &str) -> Result<Ipv4Addr, String> {
    let value = value.trim();
    let ip: Ipv4Addr = value
        .parse()
        .map_err(|_| "Enter an IPv4 address such as 192.168.1.50.".to_owned())?;
    let [first, second, _, _] = ip.octets();

    if ip.is_unspecified()
        || ip.is_loopback()
        || ip.is_link_local()
        || ip.is_multicast()
        || first == 0
        || first >= 240
        || (first == 255 && second == 255)
    {
        return Err("Use the LAN IPv4 of this computer, not a loopback, link-local, multicast, broadcast, or reserved address.".to_owned());
    }

    Ok(ip)
}

#[cfg(test)]
mod tests {
    use super::validate_host_ip;

    #[test]
    fn accepts_normal_lan_addresses() {
        assert!(validate_host_ip("192.168.1.50").is_ok());
        assert!(validate_host_ip("10.0.0.4").is_ok());
        assert!(validate_host_ip("172.20.1.2").is_ok());
    }

    #[test]
    fn rejects_unusable_addresses() {
        for value in [
            "127.0.0.1",
            "0.0.0.0",
            "0.1.2.3",
            "169.254.4.2",
            "224.0.0.1",
            "255.255.255.255",
            "not-an-ip",
        ] {
            assert!(validate_host_ip(value).is_err(), "accepted {value}");
        }
    }
}

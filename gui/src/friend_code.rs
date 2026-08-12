const PROFILE_ID_MASK: u64 = 0x7fff_ffff;
const CHECKSUM_MASK: u64 = 0x7f;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FriendCode {
    pub normalized: String,
    pub profile_id: u32,
}

pub fn validate(value: &str) -> Result<FriendCode, String> {
    let mut normalized = String::with_capacity(12);

    for character in value.chars() {
        if character.is_ascii_digit() {
            normalized.push(character);
        } else if character == '-' || character.is_ascii_whitespace() {
            continue;
        } else {
            return Err(
                "Use only the 12 digits shown in the Pal Pad (spaces and hyphens are okay)."
                    .to_owned(),
            );
        }
    }

    if normalized.len() != 12 {
        return Err(
            "Enter the complete 12-digit Friend Code shown in the game's Pal Pad.".to_owned(),
        );
    }

    let encoded = normalized
        .parse::<u64>()
        .map_err(|_| "The Friend Code could not be read. Double-check all 12 digits.".to_owned())?;
    let checksum = encoded >> 32;
    let profile_id = (encoded & PROFILE_ID_MASK) as u32;

    if checksum > CHECKSUM_MASK || profile_id == 0 {
        return Err(
            "That is not a valid Nintendo DS Friend Code. Double-check the Pal Pad.".to_owned(),
        );
    }

    Ok(FriendCode {
        normalized,
        profile_id,
    })
}

#[cfg(test)]
mod tests {
    use super::validate;

    #[test]
    fn accepts_and_normalizes_pal_pad_format() {
        let code = validate("0043-2949-6729").expect("valid friend code shape");
        assert_eq!(code.normalized, "004329496729");
        assert_eq!(code.profile_id, 34_529_433);
    }

    #[test]
    fn rejects_bad_length_characters_and_profile_ids() {
        for value in ["123", "1234-5678-90ab", "999999999999", "000000000000"] {
            assert!(validate(value).is_err(), "accepted {value}");
        }
    }
}

/// Parse strings like "1h30m", "45s", "2h5m10s" into seconds.
pub fn parse_duration(s: &str) -> Result<u64, String> {
    if s.is_empty() {
        return Err("empty".into());
    }
    let mut total = 0;
    let mut num = String::new();
    for c in s.chars() {
        if c.is_ascii_digit() {
            num.push(c);
        } else {
            let n: u64 = num.parse().map_err(|_| format!("missing number before {c}"))?;
            total = match c {
                'h' => n * 3600,
                'm' => n * 60,
                's' => n,
                _ => return Err(format!("bad unit {c}")),
            };
            num.clear();
        }
    }
    Ok(total)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn simple_units() {
        assert_eq!(parse_duration("45s"), Ok(45));
        assert_eq!(parse_duration("2h"), Ok(7200));
        assert_eq!(parse_duration("3m"), Ok(180));
    }

    #[test]
    fn combined() {
        assert_eq!(parse_duration("1h30m"), Ok(5400));
        assert_eq!(parse_duration("1h5m10s"), Ok(3910));
    }

    #[test]
    fn invalid() {
        assert!(parse_duration("").is_err());
        assert!(parse_duration("10").is_err());
        assert!(parse_duration("h").is_err());
        assert!(parse_duration("5x").is_err());
    }
}

use std::fs;
use serde::Deserialize;
use serde_json;


#[derive(Debug, Deserialize, Clone)]
pub struct CmdSpec {
    pub id: String,
    pub label: String,
    pub verb: String,
    #[serde(default)]
    pub icon: Option<String>,
    #[serde(default)]
    pub subcommands: Vec<CmdSpec>,
}


#[derive(Debug, Deserialize)]
pub struct Config {
    pub commands: Vec<CmdSpec>,
}


fn get_config() -> Config {

    let config_path = "D:/dev/projects/ftl/src/commands.json";
    let config_str = fs::read_to_string(config_path).unwrap();
    let config: Config = serde_json::from_str(&config_str).unwrap();

    println!("{:?}", config);
    println!("{:?}", config.commands);
    return config;
}

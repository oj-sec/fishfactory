use clap::Parser;
use std::{fs, env, io};
use std::path::{Path, PathBuf};
use regex::Regex;
use std::io::{BufReader, BufRead};
use std::fs::File;
use serde::{Deserialize, Serialize};
//use serde_json::Result;
//use zip::ZipArchive;

// Structs

/// Utility to extract features from phishing kits.
#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Path to the target zip file
    #[arg(short, long)]
    path: std::path::PathBuf,
}

// Struct to collect Regex match results per file
#[derive(Serialize, Deserialize)]
struct FileResult {
    filename: String,
    emailAddresses: Vec<String>,
    textFiles: Vec<String>,
    telegramTokens: Vec<String>,
    telegramChatIds: Vec<String>,
}

// Functions

// Entrypoint & main execution handler
fn main() {
    let args = Args::parse();
    let zip_name = args.path;
    
    //println!("{}",&zip_name.into_os_string().into_string().unwrap());

    let extracted_files = extract_zip_file(zip_name);

    let target_files = filter_target_files(extracted_files);

    //for file in target_files {
    //    println!("{}", file.display());
    //}

    let file_features = process_features_from_files(target_files);

    for file_feature in file_features {
        if !file_feature.emailAddresses.is_empty() || !file_feature.textFiles.is_empty() || !file_feature.telegramTokens.is_empty() || !file_feature.telegramChatIds.is_empty() {
            let serialised_file_feature = serde_json::to_string(&file_feature).unwrap();
            println!("{}",serialised_file_feature)
        }
    }

    delete_temporary_directory().unwrap();
}

// Function to create and enter a temporary working directory
fn create_temporary_directory() -> std::io::Result<()> {
    fs::create_dir("./temp/")?;
    let temp_dir = Path::new("./temp/");
    assert!(env::set_current_dir(&temp_dir).is_ok());
    Ok(())
}

// Function to extract the contents of a zip file 
// Returns a Vec of PathBufs of extracted files (omits directories)
fn extract_zip_file(zip_name:std::path::PathBuf) -> Vec<PathBuf> {

    let file = fs::File::open(&zip_name).unwrap();
    let mut archive = zip::ZipArchive::new(file).unwrap();

    create_temporary_directory().unwrap();

    let mut all_filenames: Vec<PathBuf> = Vec::new();

    for i in 0..archive.len() {
        let mut file = archive.by_index(i).unwrap();

        let outpath = match file.enclosed_name() {
            Some(path) => path.to_owned(),
            None => continue,
        };

        {
            let comment = file.comment();
            if !comment.is_empty() {
                println!("File {} comment: {}", i, comment);
            }
        }

        let outpath_clone = outpath.clone();

        if (*file.name()).ends_with('/') {
            //println!("File {} extracted to \"{}\"", i, outpath.display());
            fs::create_dir_all(&outpath).unwrap();
        } else {
            all_filenames.push(outpath_clone);
            //println!("File {} extracted to \"{}\" ({} bytes)", i, &outpath.display(), file.size());
            if let Some(p) = outpath.parent() {
                if !p.exists() {
                    fs::create_dir_all(p).unwrap();
                }
            }
            let mut outfile = fs::File::create(&outpath).unwrap();
            io::copy(&mut file, &mut outfile).unwrap();
        }

        // Get and set file permissions
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;

            if let Some(mode) = file.unix_mode() {
                fs::set_permissions(&outpath, fs::Permissions::from_mode(mode)).unwrap();
            }
        }
    }

    all_filenames
}

// Function to consume a list of files and return files of interest based on extension
fn filter_target_files(extracted_files:Vec<PathBuf>) -> Vec<PathBuf>{
    let target_extensions = ["php", "json", "txt", "js"];
    let mut filtered_files = Vec::new();
    for file in extracted_files {
        let ext = file.extension().unwrap().to_str().unwrap();
        if target_extensions.contains(&ext){
            filtered_files.push(file);
        }
    }
    filtered_files
}


// Function to consume a list of PathBufs, read each file and return matches for feature regexes
fn process_features_from_files(target_files:Vec<PathBuf>) -> Vec<FileResult> {

    let mut file_matches:Vec<FileResult> = Vec::new();

    let email_re: Regex = Regex::new(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}").unwrap();
    let txt_file_re: Regex = Regex::new(r#"(\w*?).txt\b?"#).unwrap();
    let telegram_token_re: Regex = Regex::new(r"[0-9]{8,10}:[a-zA-Z0-9_-]{35}").unwrap();
    let telegram_chat_id: Regex = Regex::new(r"[0-9]{9,12}").unwrap();
  
    for file in target_files {

        //println!("searching {}", file.display());
        let file_name = file.clone().display().to_string();
        let buffered = BufReader::new(File::open(file).unwrap());

        let mut email_re_captures: Vec<String> = Vec::new();
        let mut txt_file_re_captures: Vec<String> = Vec::new();
        let mut telegram_token_re_captures: Vec<String> = Vec::new();
        let mut telegram_chat_id_re_captures: Vec<String> = Vec::new();

        for line in buffered.lines() {

            let line_contents = line.unwrap();

            email_re_captures.extend(email_re.find_iter(line_contents.clone().as_str()).map(|mat|mat.as_str().to_string()));
            txt_file_re_captures.extend(txt_file_re.find_iter(line_contents.clone().as_str()).map(|mat|mat.as_str().to_string()));
            telegram_token_re_captures.extend(telegram_token_re.find_iter(line_contents.clone().as_str()).map(|mat|mat.as_str().to_string()));
            telegram_chat_id_re_captures.extend(telegram_chat_id.find_iter(line_contents.clone().as_str()).map(|mat|mat.as_str().to_string()));

            //let email_re_captures: Vec<String> = email_re.find_iter(line_contents.clone().as_str()).map(|mat|mat.as_str().to_string()).collect();

            //match email_re.captures(line_contents.clone().as_str()){
            //    Some(caps) => println!("Match: {}", caps.get(0).unwrap().as_str()),
            //    None => (),
            //}
            
        }

        let file_result = FileResult {
            filename: file_name.clone(),
            emailAddresses: email_re_captures.clone(),
            textFiles: txt_file_re_captures.clone(),
            telegramTokens: telegram_token_re_captures.clone(),
            telegramChatIds: telegram_chat_id_re_captures.clone(),
        };

        file_matches.push(file_result);

    }

    file_matches
}


// Function to delete the temporary directory & return to cwd
fn delete_temporary_directory() -> std::io::Result<()> {
    let cwd = Path::new("..");
    assert!(env::set_current_dir(&cwd).is_ok());
    fs::remove_dir_all("./temp/")?;
    Ok(())
}



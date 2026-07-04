#[cfg(not(debug_assertions))]
mod backend {
    use std::io::{Read, Write};
    use std::net::TcpStream;
    use std::process::{Child, Command};
    use std::sync::Mutex;
    use std::time::{Duration, Instant};

    pub struct BackendProcess(pub Mutex<Option<Child>>);

    const PORT: u16 = 8010;
    const STARTUP_TIMEOUT: Duration = Duration::from_secs(60);

    /// GET /health con stdlib puro — sin dependencia HTTP solo para un poll.
    fn health_ok() -> bool {
        let Ok(mut stream) = TcpStream::connect_timeout(
            &([127, 0, 0, 1], PORT).into(),
            Duration::from_millis(500),
        ) else {
            return false;
        };
        let _ = stream.set_read_timeout(Some(Duration::from_secs(2)));
        if stream
            .write_all(b"GET /health HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n")
            .is_err()
        {
            return false;
        }
        let mut buf = String::new();
        let _ = stream.read_to_string(&mut buf);
        buf.starts_with("HTTP/1.1 200")
    }

    /// Lanza financial-backend.exe desde resources. Devuelve None si ya hay
    /// una instancia sirviendo /health (no se lanza duplicado).
    pub fn spawn(resource_dir: &std::path::Path) -> Result<Option<Child>, String> {
        if health_ok() {
            return Ok(None);
        }
        let exe = resource_dir.join("backend").join("financial-backend.exe");
        let mut cmd = Command::new(&exe);
        cmd.current_dir(exe.parent().unwrap())
            .env("APP_ENV", "production")
            .env("BACKEND_PORT", PORT.to_string());
        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            cmd.creation_flags(0x0800_0000); // CREATE_NO_WINDOW
        }
        cmd.spawn()
            .map(Some)
            .map_err(|e| format!("no se pudo lanzar {}: {e}", exe.display()))
    }

    pub fn wait_until_healthy() -> Result<(), String> {
        let start = Instant::now();
        while start.elapsed() < STARTUP_TIMEOUT {
            if health_ok() {
                return Ok(());
            }
            std::thread::sleep(Duration::from_millis(250));
        }
        Err("el backend no respondió /health a tiempo".into())
    }

    pub fn kill(app: &tauri::AppHandle) {
        use tauri::Manager;
        if let Some(state) = app.try_state::<BackendProcess>() {
            if let Some(mut child) = state.0.lock().unwrap().take() {
                let _ = child.kill();
                let _ = child.wait();
            }
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|_app| {
            #[cfg(not(debug_assertions))]
            {
                use tauri::Manager;
                let resource_dir = _app.path().resource_dir()?;
                if let Some(child) = backend::spawn(&resource_dir)
                    .map_err(std::io::Error::other)?
                {
                    _app.manage(backend::BackendProcess(std::sync::Mutex::new(Some(child))));
                }
                // Bloquea antes de crear la ventana: /health 200 ⇒ ventana interactiva.
                backend::wait_until_healthy().map_err(std::io::Error::other)?;
            }
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|_app_handle, _event| {
        #[cfg(not(debug_assertions))]
        if matches!(_event, tauri::RunEvent::Exit) {
            backend::kill(_app_handle);
        }
    });
}

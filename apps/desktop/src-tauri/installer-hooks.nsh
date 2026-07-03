; ponytail: el sidecar financial-backend.exe puede quedar huérfano (crash,
; kill desde el Task Manager, apagado forzado) sin pasar por RunEvent::Exit
; en lib.rs, dejando bloqueados los .pyd de backend\_internal. El instalador
; solo comprueba si ai-financial-os.exe sigue vivo (CheckIfAppIsRunning), no
; el sidecar. Lo matamos aquí para que el instalador nunca falle por esto.
!macro NSIS_HOOK_PREINSTALL
  ExecWait 'taskkill.exe /F /T /IM financial-backend.exe'
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  ExecWait 'taskkill.exe /F /T /IM financial-backend.exe'
!macroend

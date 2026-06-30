type Theme = "dark" | "light";

export function useTheme() {
  const theme = (document.documentElement.getAttribute("data-theme") as Theme) || "dark";

  function setTheme(next: Theme) {
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
  }

  return { theme, setTheme };
}

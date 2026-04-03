import { MoonStar, Sun, SunMoon } from "lucide-react";
import { useTheme } from "./theme-provider";
import { Tooltip, TooltipContent, TooltipTrigger } from "./ui/tooltip";
import { Button } from "./ui/button";

export default function TernaryThemeButton({
  variant,
}: {
  variant:
    | "default"
    | "outline"
    | "secondary"
    | "ghost"
    | "destructive"
    | "link";
}) {
  const { theme, toggleTheme } = useTheme();

  const buttonIcon = () => {
    switch (theme) {
      case "system":
        return <SunMoon />;
      case "dark":
        return <MoonStar />;
      case "light":
        return <Sun />;
    }
  };

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button onClick={toggleTheme} variant={variant}>
          {buttonIcon()}
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        {theme.replace(/\w/, (char) => char.toUpperCase())}
      </TooltipContent>
    </Tooltip>
  );
}

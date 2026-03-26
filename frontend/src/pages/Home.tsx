import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { memo, useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router";
import Particles, { initParticlesEngine } from "@tsparticles/react";
import { loadSlim } from "@tsparticles/slim";

const PARTICLE_OPTIONS = {
  fullScreen: {
    enable: false,
  },
  fpsLimit: 120,
  interactivity: {
    events: {
      onHover: {
        enable: true,
        mode: "grab" as const,
      },
    },
  },
  particles: {
    color: {
      value: "#ffffff",
    },
    links: {
      color: "#ffffff",
      distance: 150,
      enable: true,
      opacity: 0.5,
      width: 2,
    },
    move: {
      direction: "none" as const,
      enable: true,
      outModes: "bounce" as const,
      random: false,
      speed: 6,
      straight: false,
    },
    number: {
      density: {
        enable: true,
      },
      value: 80,
    },
    opacity: {
      value: 0.8,
    },
    shape: {
      type: "circle",
    },
    size: {
      value: { min: 1, max: 7 },
    },
  },
  detectRetina: true,
};

const HeroParticles = memo(function HeroParticles() {
  const [particlesInitialized, setParticlesInitialized] = useState(false);

  useEffect(() => {
    initParticlesEngine(async (engine) => {
      await loadSlim(engine);
    }).then(() => {
      setParticlesInitialized(true);
    });
  }, []);

  if (!particlesInitialized) {
    return null;
  }

  return (
    <Particles
      id="particles"
      options={PARTICLE_OPTIONS}
      className="pointer-events-none absolute inset-0 z-0"
    />
  );
});

function Home() {
  const navigate = useNavigate();
  const [url, setURL] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [errorText, setErrorText] = useState("");

  const submitURL = async () => {
    // update ui - disable field input and button, change icon to Spinner
    setSubmitting(true);
    setErrorText("");

    // basic check: is it a valid url? if not, reset ui and show error
    // we'll do more comprehensive checks on the backend!
    const trimmedUrl = url.trim();
    let normalizedUrl = trimmedUrl;

    // If no scheme is present, default to http.
    if (!trimmedUrl.includes("://")) {
      normalizedUrl = `http://${trimmedUrl}`;
      setURL(normalizedUrl);
    } else {
      const schemeMatch = trimmedUrl.match(/^([a-zA-Z][a-zA-Z\d+.-]*):\/\//);
      const scheme = schemeMatch?.[1]?.toLowerCase();

      if (scheme !== "http" && scheme !== "https") {
        setErrorText("Only http:// or https:// URLs are supported.");
        setSubmitting(false);
        return;
      }
    }

    if (!URL.canParse(normalizedUrl)) {
      setErrorText("URL is not valid - please enter a valid URL.");
      setSubmitting(false);
      return;
    }

    // actually try to submit url
    const response = await fetch("/api/create", {
      body: JSON.stringify({
        url: normalizedUrl,
      }),
      headers: {
        "Content-Type": "application/json",
      },
      method: "POST",
    });

    if (response.ok) {
      // yay! let's go to the details page
      const data = await response.json();
      navigate(`/details/${data.id}`);
    } else {
      // fuck. reset ui, show the error (if we can, of course)
      try {
        const error = await response.json();
        setErrorText(error.message);
      } catch (e) {
        setErrorText("Something went wrong - please try again later.");
      }
      setSubmitting(false);
    }
  };

  const particlesGradientClass = useMemo(() => {
    if (errorText) {
      return "from-red-300 to-red-400 dark:from-red-900 dark:to-red-950";
    }

    if (submitting) {
      return "from-fuchsia-400 to-blue-400 dark:from-fuchsia-900 dark:to-blue-900";
    }

    return "from-fuchsia-300 to-blue-300 dark:from-fuchsia-950 dark:to-blue-950";
  }, [errorText, submitting]);

  return (
    <main className="min-h-screen">
      <div className="relative isolate flex h-[90vh] items-center justify-center overflow-hidden p-4">
        <div
          className={`pointer-events-none absolute inset-0 -z-10 bg-linear-to-b transition-colors duration-500 ${particlesGradientClass}`}
        />
        <HeroParticles />
        <div className="relative z-10 text-center rounded bg-white/50 dark:bg-black backdrop-blur-sm p-8">
          <h1 className="text-5xl font-semibold">ARGUS</h1>
          <p className="text-lg italic font-light">
            Analytical Reasoning and Grounded Understanding System
          </p>

          <div className="rounded-full border-2 transition border-red-400 hover:border-red-300 flex pl-2 mt-8">
            <input
              autoFocus
              type="url"
              placeholder="Enter a URL..."
              className="grow"
              onChange={(e) => setURL(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  submitURL();
                }
              }}
              value={url}
              disabled={submitting}
            />
            <Button
              variant="outline"
              size="icon"
              className="rounded-full border-red-400 border-2"
              onClick={submitURL}
              disabled={submitting}
            >
              {submitting ? <Spinner /> : <ArrowRight />}
            </Button>
          </div>
          <div className="text-red-700">{errorText}</div>
        </div>
      </div>
      <div></div>
    </main>
  );
}

export default Home;

import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router";
import Particles, { initParticlesEngine } from "@tsparticles/react";
import { loadSlim } from "@tsparticles/slim";

function Home() {
  const navigate = useNavigate();
  const [url, setURL] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [errorText, setErrorText] = useState("");
  const [particlesInitialized, setParticlesInitialized] = useState(false);

  useEffect(() => {
    initParticlesEngine(async (engine) => {
      // you can initiate the tsParticles instance (engine) here, adding custom shapes or presets
      // this loads the tsparticles package bundle, it's the easiest method for getting everything ready
      // starting from v2 you can add only the features you need reducing the bundle size
      //await loadAll(engine);
      //await loadFull(engine);
      await loadSlim(engine);
      //await loadBasic(engine);
    }).then(() => {
      setParticlesInitialized(true);
    });
  }, [])

  const submitURL = async () => {
    // update ui - disable field input and button, change icon to Spinner
    setSubmitting(true);
    setErrorText("");

    // basic check: is it a valid url? if not, reset ui and show error
    // we'll do more comprehensive checks on the backend!
    if (!URL.canParse(url)) {
      setErrorText("URL is not valid - please enter a valid URL.");
      setSubmitting(false);
      return;
    }

    // actually try to submit url
    const response = await fetch("/api/create", {
      body: JSON.stringify({
        url: url,
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

  const options = useMemo(
    () => ({
      fullScreen: {
        enable: false,
      },
      fpsLimit: 120,
      interactivity: {
        events: {
          onHover: {
            enable: true,
            mode: "grab" as const
          }
        }
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
          outModes: {
            left:  "bounce" as const,
            right: "bounce" as const
          },
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
    }),
    [],
  );

  return (
    <main className="min-h-screen">
      <div className="relative isolate flex h-[90vh] items-center justify-center overflow-hidden p-4">
        {particlesInitialized && (
          <Particles
            id="particles"
            options={options}
            className={`pointer-events-none absolute inset-0 z-0 bg-linear-to-b transition-colors duration-500 ${
              errorText
                ? "from-red-300 to-red-400"
                : submitting
                  ? "from-fuchsia-400 to-blue-400"
                  : "from-fuchsia-300 to-blue-300"
            }`}
          />
        )}
        <div className="relative z-10 text-center rounded bg-white/50 backdrop-blur-sm p-8">
          <h1 className="text-5xl font-semibold">ARGUS</h1>
          <p className="text-lg italic font-light">Analytical Reasoning and Grounded Understanding System</p>

          <div className="rounded-full border-2 transition border-red-400 bg-white hover:border-red-300 flex pl-2 mt-8">
            <input
              autoFocus
              type="url"
              placeholder="Enter a URL..."
              className="grow"
              onChange={(e) => setURL(e.target.value)}
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
      <div>
      </div>
    </main>
  );
}

export default Home;

import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { memo, useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router";
import Particles, { initParticlesEngine } from "@tsparticles/react";
import { loadSlim } from "@tsparticles/slim";
import type { CheckMetadata } from "../DetailsResponse";
import useSWR from "swr";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

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
      speed: 3,
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
      className="pointer-events-none absolute inset-0 z-0 motion-reduce:hidden dark:opacity-75"
    />
  );
});

const clampScore = (score: number) => Math.max(0, Math.min(100, score));

const getGoodnessScore = (score: number, higherIsBetter: boolean) => {
  const safeScore = clampScore(score);
  return higherIsBetter ? safeScore : 100 - safeScore;
};

const getScoreDotColorClass = (
  score: number | null | undefined,
  higherIsBetter = true,
) => {
  if (score == null) return "bg-muted";

  const goodnessScore = getGoodnessScore(score, higherIsBetter);

  if (goodnessScore === 100) return "bg-indigo-500 dark:bg-indigo-400";
  if (goodnessScore >= 90) return "bg-emerald-500 dark:bg-emerald-400";
  if (goodnessScore >= 80) return "bg-green-500 dark:bg-green-400";
  if (goodnessScore >= 60) return "bg-lime-500 dark:bg-lime-400";
  if (goodnessScore >= 40) return "bg-amber-500 dark:bg-amber-400";
  if (goodnessScore >= 20) return "bg-orange-500 dark:bg-orange-400";
  if (goodnessScore >= 10) return "bg-rose-500 dark:bg-rose-400";
  return "bg-red-600 dark:bg-red-500";
};

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
        <div className="relative z-10 text-center rounded-2xl bg-white/50 dark:bg-black/75 backdrop-blur-sm dark:backdrop-blur p-8">
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
      <div className="m-4">
        <RecentArticles />
      </div>
      {/* TODO: how work */}
    </main>
  );
}

function RecentArticles() {
  const { data, isLoading } = useSWR<CheckMetadata[]>("/api/recent_checks");

  const navigate = useNavigate();

  return (
    <div>
      <h2 className="text-xl font-bold mb-2">Recent Articles</h2>
      <div className="p-2">
        {isLoading && (
          <>
            <Spinner />
          </>
        )}
        {data && (
          <>
            {data
              .sort(
                (a, b) =>
                  Date.parse(b.fact_check_metadata.check_submitted) -
                  Date.parse(a.fact_check_metadata.check_submitted),
              )
              .map((article) => (
                <Card key={article.id}>
                  <CardHeader>
                    <CardTitle>{article.article_metadata.title}</CardTitle>
                    <CardDescription>
                      {article.article_metadata.sitename}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <span className="line-clamp-3">{article.summary}</span>
                    <div className="items-center justify-center flex pt-2">
                      {/* a dot (with tooltip) for each rating */}
                      {/* completeness, accuracy, political, sensationalism, emotional language */}
                      {/* Completeness */}
                      <Tooltip>
                        <TooltipTrigger>
                          <div
                            className={`w-3 h-3 rounded-full mx-1 ${getScoreDotColorClass(article.completeness_score)}`}
                          />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Completeness: {article.completeness_score}</p>
                        </TooltipContent>
                      </Tooltip>
                      {/* Accuracy */}
                      <Tooltip>
                        <TooltipTrigger>
                          <div
                            className={`w-3 h-3 rounded-full mx-1 ${getScoreDotColorClass(article.accuracy_score)}`}
                          />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Accuracy: {article.accuracy_score}</p>
                        </TooltipContent>
                      </Tooltip>
                      <Tooltip>
                        <TooltipTrigger>
                          <div
                            className={`w-3 h-3 rounded-full mx-1 ${getScoreDotColorClass(article.political_score, false)}`}
                          />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Political: {article.political_score}</p>
                        </TooltipContent>
                      </Tooltip>
                      <Tooltip>
                        <TooltipTrigger>
                          <div
                            className={`w-3 h-3 rounded-full mx-1 ${getScoreDotColorClass(article.sensationalism_score, false)}`}
                          />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Sensationalism: {article.sensationalism_score}</p>
                        </TooltipContent>
                      </Tooltip>
                      <Tooltip>
                        <TooltipTrigger>
                          <div
                            className={`w-3 h-3 rounded-full mx-1 ${getScoreDotColorClass(article.emotional_language_score, false)}`}
                          />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>
                            Emotional Language:{" "}
                            {article.emotional_language_score}
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    </div>
                  </CardContent>
                  <CardFooter>
                    <Button
                      variant="outline"
                      size="lg"
                      onClick={() => {
                        navigate(`/details/${article.id}`);
                      }}
                    >
                      <ArrowRight /> View Details
                    </Button>
                    <span className="ml-auto text-sm text-muted-foreground">
                      {new Date(
                        article.fact_check_metadata.check_submitted,
                      ).toLocaleString()}
                    </span>
                  </CardFooter>
                </Card>
              ))}
          </>
        )}
      </div>
    </div>
  );
}

export default Home;

import { useParams } from "react-router-dom";
import { Separator } from "@/components/ui/separator";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Clock, Bot, Flag } from "lucide-react";
import { useState } from "react";
import { Spinner } from "@/components/ui/spinner";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import prettyMilliseconds from "pretty-ms";
import { Button } from "@/components/ui/button";
import {
  PrettyDuration,
  PrettyDynamicDuration,
} from "@/components/PrettyDuration";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import type { CheckMetadata } from "../DetailsResponse";
import useSWR from "swr";
import { Fade, Fades } from "@/components/animate-ui/primitives/effects/fade";
import {
  Avatar,
  AvatarFallback,
  AvatarGroup,
  AvatarImage,
} from "@/components/ui/avatar";
import {
  Drawer,
  DrawerContent,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
  DrawerClose,
} from "@/components/ui/drawer";

type StatusFetchError = Error & {
  status?: number;
};

type ScoreAssessmentCardProps = {
  title: string;
  score: number | null | undefined;
  description: string | null | undefined;
  higherIsBetter?: boolean;
  sources: string[] | undefined;
};

const clampScore = (score: number) => Math.max(0, Math.min(100, score));

const getGoodnessScore = (score: number, higherIsBetter: boolean) => {
  const safeScore = clampScore(score);
  return higherIsBetter ? safeScore : 100 - safeScore;
};

const getScoreBarColorClass = (score: number, higherIsBetter: boolean) => {
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

const animationTimings = {
  notFoundTitle: 60,
  notFoundBody: 120,
  title: 50,
  metadata: 120,
  separator: 180,
  cardsRowOne: 240,
  cardsRowTwo: 320,
  cardsRowThree: 400,
  cardStagger: 70,
  footerDisclaimer: 500,
  footerReport: 560,
  statusInitialOpacity: 0.35,
  statusTransition: { duration: 0.25 },
} as const;

export const statusFetcher = async ([url, uuid]: [string, string]) => {
  const response = await fetch(url, {
    body: JSON.stringify({
      uuid,
    }),
    headers: {
      "Content-Type": "application/json",
    },
    method: "POST",
  });

  if (!response.ok) {
    const error = new Error(
      "Failed to fetch article status",
    ) as StatusFetchError;
    error.status = response.status;
    throw error;
  }

  return (await response.json()) as CheckMetadata;
};

function DetailsView() {
  const { id } = useParams();
  const { data, error } = useSWR<CheckMetadata, StatusFetchError>(
    id ? ["/api/status", id] : null,
    statusFetcher,
    {
      refreshInterval: (latestData) => (latestData?.finished ? 0 : 5000),
      revalidateOnFocus: true,
      shouldRetryOnError: (fetchError) => fetchError.status !== 404,
    },
  );
  const analysisComplete = data?.finished ?? false;
  const notFound = error?.status === 404;

  if (notFound) {
    return (
      <main className="p-4">
        <Fade asChild delay={animationTimings.notFoundTitle}>
          <h1 className="font-semibold text-2xl text-pretty">
            Article Not Found
          </h1>
        </Fade>
        <Fade asChild delay={animationTimings.notFoundBody}>
          <p className="text-muted-foreground">
            We couldn't find an analysis for this article. It may have been
            removed, or the URL may be incorrect.
          </p>
        </Fade>
      </main>
    );
  }

  return (
    <main className="p-4">
      <Fade asChild delay={animationTimings.title}>
        <h1 className="font-semibold text-2xl text-pretty">
          <a
            href={data?.article_metadata?.url || ""}
            className="hover:underline"
          >
            {data?.article_metadata?.title || "TBD"}
          </a>
        </h1>
      </Fade>
      <Fade asChild delay={animationTimings.metadata}>
        <div className="sm:flex items-center text-muted-foreground">
          <a
            href={
              (data &&
                data.article_metadata &&
                data.article_metadata.url &&
                new URL(data?.article_metadata?.url).origin) ||
              ""
            }
            className="flex items-center hover:underline"
          >
            <img
              src={`${data && data.article_metadata && data.article_metadata.url && new URL(data?.article_metadata.url).origin}/favicon.ico`}
              alt={`${data?.article_metadata?.sitename || "ARGUS"} Logo`}
              className="h-6 mr-2 rounded bg-gray-300/50"
            />
            <p className="italic text-lg">
              {data?.article_metadata?.sitename || "ARGUS"}
            </p>
          </a>
          <Separator orientation="vertical" className="mx-4" />
          <Tooltip>
            <TooltipTrigger className="flex items-center">
              <Clock className="mr-2" />
              {data && data.article_metadata && data.article_metadata.date ? (
                <p>
                  Published{" "}
                  {prettyMilliseconds(
                    Date.now() - Date.parse(data?.article_metadata.date),
                    { verbose: true, compact: true },
                  )}{" "}
                  ago
                </p>
              ) : (
                <></>
              )}
            </TooltipTrigger>
            <TooltipContent>
              <p>
                {new Date(data?.article_metadata?.date).toLocaleDateString()}
              </p>
            </TooltipContent>
          </Tooltip>
          <Separator orientation="vertical" className="mx-4" />
          <Tooltip>
            <TooltipTrigger className="flex items-center">
              {/* only show spinner when analysis is in progress */}
              {analysisComplete ? (
                <Fade
                  key="analysis-complete"
                  className="flex items-center"
                  initialOpacity={animationTimings.statusInitialOpacity}
                  transition={animationTimings.statusTransition}
                >
                  <Bot className="mr-2" />
                  <p>Analysis Complete</p>
                </Fade>
              ) : (
                <Fade
                  key="analysis-progress"
                  className="flex items-center"
                  initialOpacity={animationTimings.statusInitialOpacity}
                  transition={animationTimings.statusTransition}
                >
                  <Spinner className="mr-2" />
                  <p>
                    {data?.fact_check_metadata?.check_started
                      ? "Analysis In Progress..."
                      : "Analysis Pending..."}
                  </p>
                </Fade>
              )}
            </TooltipTrigger>
            <TooltipContent>
              <p>
                {analysisComplete ? (
                  <>
                    <span>Duration: </span>
                    <PrettyDuration
                      milliseconds={
                        (data?.fact_check_metadata.check_duration_from_start ??
                          0) * 1000
                      }
                    />
                  </>
                ) : data?.fact_check_metadata?.check_started ? (
                  <>
                    <span>Elapsed: </span>
                    <PrettyDynamicDuration
                      date={
                        new Date(
                          data?.fact_check_metadata.check_started ?? Date.now(),
                        )
                      }
                      msOpts={{
                        secondsDecimalDigits: 0,
                      }}
                    />
                  </>
                ) : (
                  <>
                    <span>Queued: </span>
                    <PrettyDynamicDuration
                      date={
                        new Date(
                          data?.fact_check_metadata.check_submitted ??
                            Date.now(),
                        )
                      }
                      msOpts={{
                        secondsDecimalDigits: 0,
                      }}
                    />
                  </>
                )}
              </p>
            </TooltipContent>
          </Tooltip>
        </div>
      </Fade>
      <Fade asChild delay={animationTimings.separator}>
        <Separator className="mt-4 mb-2" />
      </Fade>
      <div className="grid grid-cols-1 gap-4 py-2">
        <Fades
          className="h-full"
          delay={animationTimings.cardsRowOne}
          holdDelay={animationTimings.cardStagger}
        >
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Article Summary</CardTitle>
            </CardHeader>
            <CardContent>
              {data && data.summary != null ? (
                <p>{data.summary}</p>
              ) : (
                <>
                  <Skeleton className="h-4 w-full mb-2" />
                  <Skeleton className="h-4 w-full mb-2" />
                  <Skeleton className="h-4 w-full mb-2" />
                  <Skeleton className="h-4 w-full mb-2" />
                  <Skeleton className="h-4 w-1/4 mb-2" />
                </>
              )}
            </CardContent>
          </Card>
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Key Points</CardTitle>
            </CardHeader>
            <CardContent>
              {data && data.key_points.length !== 0 ? (
                <ul className="list-disc pl-5 space-y-1">
                  {data.key_points.map((point, index) => (
                    <li key={index}>{point}</li>
                  ))}
                </ul>
              ) : (
                <>
                  <Skeleton className="h-4 w-1/2 mb-2" />
                  <Skeleton className="h-4 w-1/2 mb-2" />
                  <Skeleton className="h-4 w-1/2 mb-2" />
                </>
              )}
            </CardContent>
          </Card>
        </Fades>
      </div>
      <div className="grid sm:grid-cols-2 gap-4 py-2">
        <Fades
          className="h-full"
          delay={animationTimings.cardsRowTwo}
          holdDelay={animationTimings.cardStagger}
        >
          <ScoreAssessmentCard
            title="Completeness Assessment"
            score={data?.completeness_score}
            description={data?.completeness_explanation}
            sources={data?.completeness_sources}
          />
          <ScoreAssessmentCard
            title="Accuracy Assessment"
            score={data?.accuracy_score}
            description={data?.accuracy_explanation}
            sources={data?.accuracy_sources}
          />
        </Fades>
      </div>
      <div className="grid sm:grid-cols-3 gap-4 py-2">
        <Fades
          className="h-full"
          delay={animationTimings.cardsRowThree}
          holdDelay={animationTimings.cardStagger}
        >
          <ScoreAssessmentCard
            title="Political Assessment"
            score={data?.political_score}
            description={data?.political_bias}
            higherIsBetter={false}
          />
          <ScoreAssessmentCard
            title="Sensationalism Assessment"
            score={data?.sensationalism_score}
            description={data?.sensationalism}
            higherIsBetter={false}
          />
          <ScoreAssessmentCard
            title="Emotional Language Assessment"
            score={data?.emotional_language_score}
            description={data?.emotional_language}
            higherIsBetter={false}
          />
        </Fades>
      </div>
      <Fade asChild delay={animationTimings.footerDisclaimer}>
        <div className="flex text-muted-foreground items-center justify-center">
          <Bot />
          <span className="max-w-4/5">
            ARGUS is built on top of LLMs and can make mistakes. Please
            double-check responses.
          </span>
        </div>
      </Fade>
      <Fade asChild delay={animationTimings.footerReport}>
        <div className="flex items-center justify-center p-2">
          <ReportAConcern />
        </div>
      </Fade>
    </main>
  );
}

function ScoreAssessmentCard({
  title,
  score,
  description,
  sources = undefined,
  higherIsBetter = true,
}: ScoreAssessmentCardProps) {
  const safeScore = score != null ? clampScore(score) : 0;
  const barColorClass =
    score != null ? getScoreBarColorClass(score, higherIsBetter) : "";

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {score != null ? (
          <>
            <div className="content-center">
              <div className="flex items-baseline">
                <p className="text-4xl font-bold pr-1">{safeScore}</p>
                <p className="text-muted-foreground">out of 100</p>
              </div>
              <div className="w-full bg-muted rounded-full h-4 mt-1 mb-4 overflow-hidden">
                <div
                  className={`h-4 rounded-full transition-[width,background-color] duration-500 ${barColorClass}`}
                  style={{ width: `${safeScore}%` }}
                />
              </div>
            </div>
            <p className="mb-2">{description}</p>
            {sources !== undefined && <Sources sources={sources} />}
          </>
        ) : (
          <>
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-1/4 mb-2" />
          </>
        )}
      </CardContent>
    </Card>
  );
}

function ReportAConcern() {
  const { id } = useParams();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [reportText, setReportText] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [retrying, setRetrying] = useState(false);

  const submitReport = async () => {
    await fetch("/api/report", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        report: reportText,
        fact_check_id: id,
      }),
    });
    await new Promise((resolve) => setTimeout(resolve, 1000));
  };

  const retryArticle = async () => {
    const response = await fetch("/api/retry", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        uuid: id,
      }),
    });
    if (response.ok) {
      window.location.reload();
    }
  };

  return (
    <Dialog open={dialogOpen} onOpenChange={(open) => setDialogOpen(open)}>
      <DialogTrigger className="w-full">
        <Button variant="destructive" className="w-[50%]">
          <Flag />
          Report a Concern
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Report a Concern</DialogTitle>
          <DialogDescription>
            If you believe there is an issue with the analysis of this article,
            please let us know! We will review the report, and use it to help
            improve ARGUS.
          </DialogDescription>
        </DialogHeader>
        <Textarea
          placeholder="What's wrong with the analysis of this article?"
          className="w-full h-32 mb-4"
          value={reportText}
          onChange={(e) => setReportText(e.target.value)}
        />
        <DialogFooter>
          <DialogClose />
          <Button
            variant="destructive"
            disabled={submitting || retrying}
            onClick={async () => {
              setRetrying(true);
              await submitReport();
              await retryArticle();
              setRetrying(false);
            }}
          >
            {retrying ? <Spinner /> : <></>}
            Submit & Retry
          </Button>
          <Button
            variant="destructive"
            disabled={submitting || retrying}
            onClick={async () => {
              setSubmitting(true);
              await submitReport();
              setSubmitting(false);
              setDialogOpen(false);
            }}
          >
            {submitting ? <Spinner /> : <></>}
            Submit Report
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function Sources({ sources }: { sources: string[] }) {
  return (
    <>
      <Drawer>
        <DrawerTrigger>
          <div className="flex">
            <span className="pr-2 text-md text-muted-foreground items-center">
              Sources
            </span>
            <AvatarGroup>
              {sources.slice(0, 3).map((_url) => (
                <Avatar size="sm">
                  <AvatarImage src="" alt="" />
                  <AvatarFallback>:3</AvatarFallback>
                </Avatar>
              ))}
            </AvatarGroup>
          </div>
        </DrawerTrigger>
        <DrawerContent>
          <DrawerHeader>
            <DrawerTitle>Sources</DrawerTitle>
          </DrawerHeader>
          <div className="no-scrollbar overflow-y-auto px-4"></div>
          <DrawerFooter>
            <DrawerClose asChild>
              <Button variant="outline">Close</Button>
            </DrawerClose>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>
    </>
  );
}

export default DetailsView;

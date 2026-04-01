import { useParams } from "react-router-dom";
import { Separator } from "@/components/ui/separator";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Clock, Bot, Flag } from "lucide-react";
import { useEffect, useState } from "react";
import { Spinner } from "@/components/ui/spinner";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useInterval } from "usehooks-ts";
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

interface DetailsResponse {
  url: string;
  id: string;
  fact_check_metadata: Record<string, any>;
  article_text: string;
  summary: string | null;
  bias_rating: string | null;
  key_points: string[];
  article_metadata: Record<string, any>;
  accuracy_score: number | null;
  completeness_score: number | null;
  accuracy_explanation: string | null;
  completeness_explanation: string | null;
  sources: string[];
  political_bias: string | null;
  sensationalism: string | null;
  emotional_language: string | null;
  political_score: number | null;
  sensationalism_score: number | null;
  emotional_language_score: number | null;
  finished: boolean;
}

function DetailsView() {
  const { id } = useParams();
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [data, setData] = useState<DetailsResponse | null>(null);

  const fetchData = async () => {
    if (!analysisComplete) {
      const response = await fetch(`/api/status`, {
        body: JSON.stringify({
          uuid: id,
        }),
        headers: {
          "Content-Type": "application/json",
        },
        method: "POST",
      });
      const data = await response.json();
      if (data.finished) {
        setAnalysisComplete(true);
      }
      setData(data);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);
  useInterval(fetchData, 5000);

  return (
    <main className="p-4">
      <h1 className="font-semibold text-2xl text-pretty">
        <a href={data?.article_metadata.url} className="hover:underline">
          {data?.article_metadata.title}
        </a>
      </h1>
      <div className="sm:flex items-center text-muted-foreground">
        <a
          href={(data && new URL(data?.article_metadata.url).origin) || ""}
          className="flex items-center hover:underline"
        >
          <img
            src={`${data && new URL(data?.article_metadata.url).origin}/favicon.ico`}
            alt={`${data?.article_metadata.sitename || "ARGUS"} Logo`}
            className="h-6 mr-2 rounded bg-gray-300/50"
          />
          <p className="italic text-lg">{data?.article_metadata.sitename}</p>
        </a>
        <Separator orientation="vertical" className="mx-4" />
        <Tooltip>
          <TooltipTrigger className="flex items-center">
            <Clock className="mr-2" />
            {data && data.article_metadata && data.article_metadata.date ? (
              <p>
                Published{" "}
                {prettyMilliseconds(
                  Date.now() - new Date(data?.article_metadata.date),
                  { verbose: true, compact: true },
                )}{" "}
                ago
              </p>
            ) : (
              <></>
            )}
          </TooltipTrigger>
          <TooltipContent>
            <p>{new Date(data?.article_metadata.date).toLocaleDateString()}</p>
          </TooltipContent>
        </Tooltip>
        <Separator orientation="vertical" className="mx-4" />
        <Tooltip>
          <TooltipTrigger className="flex items-center">
            {/* only show spinner when analysis is in progress */}
            {analysisComplete ? (
              <>
                <Bot className="mr-2" />
                <p>Analysis Complete</p>
              </>
            ) : (
              <>
                <Spinner className="mr-2" />
                <p>Analysis In Progress...</p>
              </>
            )}
          </TooltipTrigger>
          <TooltipContent>
            <p>
              {analysisComplete ? (
                <>
                  <span>Duration: </span>
                  <PrettyDuration
                    milliseconds={
                      data?.fact_check_metadata.check_duration_from_start * 1000
                    }
                  />
                </>
              ) : (
                <>
                  <span>Elapsed: </span>
                  <PrettyDynamicDuration
                    date={new Date(data?.fact_check_metadata.check_started)}
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
      <Separator className="mt-4 mb-2" />
      <div className="grid grid-cols-1 gap-4 py-2">
        <Card>
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
        <Card>
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
      </div>
      <div className="grid sm:grid-cols-2 gap-4 py-2">
        <Card>
          <CardHeader>
            <CardTitle>Completeness Assessment</CardTitle>
          </CardHeader>
          <CardContent>
            {data && data.completeness_score != null ? (
              <>
                <p>Score: {data.completeness_score}/100</p>
                <p>{data.completeness_explanation}</p>
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
        <Card>
          <CardHeader>
            <CardTitle>Accuracy Assessment</CardTitle>
          </CardHeader>
          <CardContent>
            {data && data.accuracy_score != null ? (
              <>
                <p>Score: {data.accuracy_score}/100</p>
                <p>{data.accuracy_explanation}</p>
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
      </div>
      <div className="grid sm:grid-cols-3 gap-4 py-2">
        <Card>
          <CardHeader>
            <CardTitle>Political Assessment</CardTitle>
          </CardHeader>
          <CardContent>
            {data && data.political_score != null ? (
              <>
                <p>Score: {data.political_score}/100</p>
                <p>{data.political_bias}</p>
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
        <Card>
          <CardHeader>
            <CardTitle>Sensationalism Assessment</CardTitle>
          </CardHeader>
          <CardContent>
            {data && data.sensationalism_score != null ? (
              <>
                <p>Score: {data.sensationalism_score}/100</p>
                <p>{data.sensationalism}</p>
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
        <Card>
          <CardHeader>
            <CardTitle>Emotional Language Assessment</CardTitle>
          </CardHeader>
          <CardContent>
            {data && data.emotional_language_score != null ? (
              <>
                <p>Score: {data.emotional_language_score}/100</p>
                <p>{data.emotional_language}</p>
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
      </div>
      <div className="flex text-muted-foreground items-center justify-center">
        <Bot />
        <span className="max-w-4/5">
          ARGUS is built on top of LLMs and can make mistakes. Please
          double-check responses.
        </span>
      </div>
      <div className="flex items-center justify-center p-2">
        <ReportAConcern />
      </div>
    </main>
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
    // TODO: just call the regular submission endpoint, just get another check
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
            onClick={async (e) => {
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
            onClick={async (e) => {
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

export default DetailsView;

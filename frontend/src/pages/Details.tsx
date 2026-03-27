import { useParams } from "react-router-dom";
import { Separator } from "@/components/ui/separator";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Clock, Bot, Flag } from "lucide-react";
import { useEffect, useState, useRef } from "react";
import { Spinner } from "@/components/ui/spinner";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useInterval, useTimeout } from "usehooks-ts";
import prettyMilliseconds from "pretty-ms";
import { Button } from "@/components/ui/button";

interface DetailsResponse {
  url: string;
  id: string;
  article_text: string;
  summary: string | null;
  bias_rating: string | null;
  key_points: string[];
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

  fetchData();
  useInterval(fetchData, 5000);

  return (
    <main className="p-4">
      <h1 className="font-semibold text-2xl text-pretty">
        {analysisComplete
          ? "ChatGPT Convinces Sam Altman to Kill Humanity"
          : "placeholder (title)"}
      </h1>
      <div className="flex items-center text-muted-foreground">
        <img
          src="https://placehold.co/24"
          alt="The Guardian Logo"
          className="h-6 mr-2 rounded"
        />
        <p className="italic text-lg">
          {analysisComplete ? "The Onion" : "placeholder (site name)"}
        </p>
        <Separator orientation="vertical" className="mx-4" />
        <Tooltip>
          <TooltipTrigger className="flex items-center">
            <Clock className="mr-2" />
            <p>
              Published{" "}
              {prettyMilliseconds(1000, { verbose: true, compact: true })} ago
            </p>
          </TooltipTrigger>
          <TooltipContent>
            <p>March 11, 2026 11:00 AM EDT</p>
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
              {analysisComplete
                ? "Analysis complete"
                : "Analysis in progress..."}
            </p>
          </TooltipContent>
        </Tooltip>
      </div>
      <Separator className="my-4" />
      <div className="grid grid-cols-1 gap-4">
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
      <div className="grid grid-cols-2 gap-4 py-4">
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
        ARGUS is built on top of LLMs and can make mistakes. Please double-check
        respones.
      </div>
      <div className="flex items-center justify-center p-2">
        <Button variant="destructive" className="w-[50%]">
          <Flag />
          Report a Concern
        </Button>
      </div>
    </main>
  );
}

export default DetailsView;

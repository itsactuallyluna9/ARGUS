import { useParams } from "react-router-dom";
import { Separator } from "@/components/ui/separator";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Clock, Bot } from "lucide-react";
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
import { useInterval } from "usehooks-ts";
import prettyMilliseconds from "pretty-ms";

interface DetailsResponse {
  url: string;
  id: string;
  article_text: string;
  summary: string;
  bias_rating: string;
  key_points: string[];
  accuracy_score: number;
  completeness_score: number;
  accuracy_explanation: string;
  completeness_explanation: string;
  sources: string[];
  political_bias: string;
  sensationalism: string;
  emotional_language: string;
  political_score: number;
  sensationalism_score: number;
  emotional_language_score: number;
  finished: boolean;
}

function DetailsView() {
  const { id } = useParams();
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [data, setData] = useState<DetailsResponse | null>(null);

  useInterval(async () => {
    if (!analysisComplete) {
      const response = await fetch(`/api/status`, {
        body: JSON.stringify({
          uuid: id
        }),
        headers: {
          "Content-Type": "application/json"
        },
        method: "POST"
      });
      const data = await response.json();
      if (data.finished) {
        setAnalysisComplete(true);
      }
      setData(data)
    }
  }, 5000);

  return (
    <main className="p-4">
      <h1 className="font-semibold text-2xl">placeholder (title)</h1>
      <div className="flex items-center text-muted-foreground">
        <img
          src="https://placehold.co/24"
          alt="The Guardian Logo"
          className="h-6 mr-2 rounded"
        />
        <p className="italic text-lg">placeholder (site name)</p>
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
      <Card>
        <CardHeader>
          <CardTitle>Article Summary</CardTitle>
        </CardHeader>
        <CardContent>
          {(data && data.summary !== "Empty for now!") ? (
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
          {(data && data.key_points) ? (
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
      <Card>
        <CardHeader>
          <CardTitle>Completeness Assessment</CardTitle>
        </CardHeader>
        <CardContent>
          {(data && data.completeness_score) ? (
            <>
              <p>Score: {data.completeness_score}/100</p>
              <p>{data.completeness_explanation}</p>
            </>
          ) : (
            <>
              <Skeleton className="h-4 w-1/4 mb-2" />
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-4 w-full mb-2" />
            </>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Accuracy Assessment</CardTitle>
        </CardHeader>
        <CardContent>
          {(data && data.accuracy_score) ? (
            <>
              <p>Score: {data.accuracy_score}/100</p>
              <p>{data.accuracy_explanation}</p>
            </>
          ) : (
            <>
              <Skeleton className="h-4 w-1/4 mb-2" />
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-4 w-full mb-2" />
            </>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Political Assessment</CardTitle>
        </CardHeader>
        <CardContent>
          {(data && data.political_score) ? (
            <>
              <p>Score: {data.political_score}/100</p>
              <p>{data.political_bias}</p>
            </>
          ) : (
            <>
              <Skeleton className="h-4 w-1/4 mb-2" />
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-4 w-full mb-2" />
            </>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Sensationalism Assessment</CardTitle>
        </CardHeader>
        <CardContent>
          {(data && data.sensationalism_score) ? (
            <>
              <p>Score: {data.sensationalism_score}/100</p>
              <p>{data.sensationalism}</p>
            </>
          ) : (
            <>
              <Skeleton className="h-4 w-1/4 mb-2" />
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-4 w-full mb-2" />
            </>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Emotional Language Assessment</CardTitle>
        </CardHeader>
        <CardContent>
          {(data && data.emotional_language_score) ? (
            <>
              <p>Score: {data.emotional_language_score}/100</p>
              <p>{data.emotional_language}</p>
            </>
          ) : (
            <>
              <Skeleton className="h-4 w-1/4 mb-2" />
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-4 w-full mb-2" />
            </>
          )}
        </CardContent>
      </Card>
    </main>
  );
}

export default DetailsView;

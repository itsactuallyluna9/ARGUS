import { useParams } from "react-router-dom";
import { Separator } from "@/components/ui/separator";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Clock } from "lucide-react";
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
  related_summaries: Summary[];
  accuracy_score: number;
  completeness_score: number;
  accuracy_explanation: string;
  completeness_explanation: string;
  sources: string[];
  finished: boolean;
}

interface Summary {
  summary: string;
  url: string;
}

function DetailsView() {
  const { id } = useParams();
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [_data, setData] = useState<DetailsResponse | null>(null);

  useInterval(async () => {
    if (!analysisComplete) {
      const response = await fetch(`/api/get/${id}`);
      const data = await response.json();
      if (data.finished) {
        setAnalysisComplete(true);
      }
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
            <Spinner className="mr-2" />
            <p>Analysis {analysisComplete ? "Complete" : "In Progress..."}</p>
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
          {_data ? (
            <p>{_data.summary}</p>
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
          {_data ? (
            <ul className="list-disc pl-5 space-y-1">
              {_data.key_points.map((point, index) => (
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
          <CardTitle>Cross-References (placeholder)</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Summary</TableHead>
                <TableHead>Original Article</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {_data ? (
                _data.related_summaries.map((ref, index) => (
                  <TableRow key={index}>
                    <TableCell>{ref[0] || "Generation error :c"}</TableCell>
                    <TableCell>{ref[1]}</TableCell>
                  </TableRow>
                ))
              ) : (
                <>
                  <TableRow>
                    <TableCell>
                      <Skeleton className="h-4 w-full mb-2" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-4 w-full mb-2" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>
                      <Skeleton className="h-4 w-full mb-2" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-4 w-full mb-2" />
                    </TableCell>
                  </TableRow>
                </>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Completeness Assessment</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-3/4 mb-2" />
        </CardContent>
      </Card>
    </main>
  );
}

export default DetailsView;

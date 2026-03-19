import { useParams } from 'react-router-dom'
import { Separator } from '@/components/ui/separator'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Clock } from 'lucide-react'
import { useState } from 'react'
import { useInterval } from 'usehooks-ts'
import { Spinner } from '@/components/ui/spinner'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'


function DetailsView() {
  const { id } = useParams()
  const [analysisComplete, setAnalysisComplete] = useState(false) // while this is false we have to keep reloading

  useInterval(async () => {
    if (!analysisComplete) {
      const response = await fetch(`/api/get/${id}`)
      const data = await response.json()
      if (data.complete) {
        setAnalysisComplete(true)
      }
    }
  }, 5000)
  
  return (
    <main className="p-4">
      <h1 className="font-semibold text-2xl">'I took two bites and had to spit it out': candy makers are phasing real cocoa in chocolate</h1>
      <div className="flex items-center text-muted-foreground">
        <img src="https://placehold.co/24" alt="The Guardian Logo" className="h-6 mr-2 rounded" />
        <p className="italic text-lg">The Guardian</p>
        <Separator orientation="vertical" className="mx-4" />
        <Tooltip>
          <TooltipTrigger className="flex items-center">
            <Clock className="mr-2" />
            <p>Published 1 day ago</p>
          </TooltipTrigger>
          <TooltipContent>
            <p>March 11, 2026 11:00 AM EDT</p>
          </TooltipContent>
        </Tooltip>
        <Separator orientation="vertical" className="mx-4" />
        <Tooltip>
          <TooltipTrigger className="flex items-center">
            <Spinner className="mr-2" />
            <p>Analysis {analysisComplete ? 'Complete' : 'In Progress...'}</p>
          </TooltipTrigger>
          <TooltipContent>
            <p>{analysisComplete ? 'Analysis complete' : 'Analysis in progress...'}</p>
          </TooltipContent>
        </Tooltip>
      </div>
      <Separator className='my-4' />
      <Card>
        <CardHeader>
          <CardTitle>Article Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-1/4 mb-2" />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Cross-References</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Reference</TableHead>
                <TableHead>Description</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell><a href="https://www.scientificamerican.com/article/why-chocolate-is-so-hard-to-make-without-cocoa1/">Why Chocolate Is So Hard to Make Without Cocoa</a></TableCell>
                <TableCell>Scientific American article on the challenges of making chocolate without cocoa.</TableCell>
              </TableRow>
              <TableRow>
                <TableCell><a href="https://www.nature.com/news/2005/050430/full/news050430-17.html">The bitter and the sweet</a></TableCell>
                <TableCell>Nature article discussing the science of chocolate flavor and the role of cocoa.</TableCell>
              </TableRow>
              <TableRow>
                <TableCell><a href="https://www.cbc.ca/radio/quirks/august-29-2020-science-of-chocolate-and-cocoa-pods-and-more-1.5706347">The Science of Chocolate and Cocoa Pods</a></TableCell>
                <TableCell>CBC Radio Quirks episode exploring the science behind chocolate and cocoa pods.</TableCell>
              </TableRow>
            </TableBody>
          </Table>
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
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
  )
}

export default DetailsView

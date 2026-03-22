import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

function Debug() {
  return (
    <main className="p-4">
      <h1 className="font-semibold text-2xl">Debug Page</h1>
      <div className="flex gap-4">
        <Card className="w-1/2">
          <CardHeader>
            <CardTitle>Resource Utilization</CardTitle>
          </CardHeader>
          <CardContent></CardContent>
        </Card>
        <Card className="w-1/2">
          <CardHeader>
            <CardTitle>Statistics</CardTitle>
          </CardHeader>
          <CardContent></CardContent>
        </Card>
        <Card className="w-1/2">
          <CardHeader>
            <CardTitle>Loaded Models</CardTitle>
          </CardHeader>
          <CardContent></CardContent>
        </Card>
      </div>
      <Separator className="my-4" />
      <Card>
        <CardHeader>
          <CardTitle>Model API</CardTitle>
        </CardHeader>
        <CardContent></CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Bulk Import</CardTitle>
        </CardHeader>
        <CardContent></CardContent>
      </Card>
    </main>
  );
}

export default Debug;

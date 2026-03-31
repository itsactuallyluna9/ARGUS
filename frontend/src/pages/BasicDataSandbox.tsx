import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Cat, FlaskConical } from "lucide-react";

export default function BasicDataSandboxView() {
  return (
    <>
      <div className="flex justify-bottom items-bottom px-2">
        <h1 className="font-semibold text-2xl">Data Sandbox</h1>
        <div className="grow"></div>
        <Button variant="link">
          <FlaskConical />
          Advanced
        </Button>
      </div>
      <Separator className="my-2" />
      <main>
        Placeholder
        <Button variant="ghost">
          <Cat /> :3
        </Button>
      </main>
    </>
  );
}

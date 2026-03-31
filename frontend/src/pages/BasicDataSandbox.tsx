import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Cat, FlaskConical } from "lucide-react";
import { Link } from "react-router-dom";

export default function BasicDataSandboxView() {
  return (
    <>
      <main className="p-2">
        <div className="flex justify-bottom items-bottom">
          <h1 className="font-semibold text-2xl">Data Sandbox</h1>
          <div className="grow"></div>
          <Link to="/sandbox/advanced">
            <Button variant="link">
              <FlaskConical />
              Advanced
            </Button>
          </Link>
        </div>
        <Separator className="my-2" />
        Placeholder
        <Button variant="ghost">
          <Cat /> :3
        </Button>
      </main>
    </>
  );
}

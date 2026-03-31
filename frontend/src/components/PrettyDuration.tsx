import prettyMilliseconds, { type Options } from "pretty-ms";
import { useEffect, useState } from "react";

export function PrettyDuration({
  milliseconds,
  msOpts = {},
}: {
  milliseconds: number;
  msOpts?: Options;
}) {
  return <>{prettyMilliseconds(milliseconds, msOpts)}</>;
}

export function useTime(resolution: number) {
  const [time, setTime] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => {
      setTime(new Date());
    }, resolution);
    return () => clearInterval(id);
  }, [resolution]);
  return time;
}

export function PrettyDynamicDuration({
  date,
  timeResolution = 1000,
  msOpts = {},
}: {
  date: Date;
  timeResolution?: number;
  msOpts?: Options;
}) {
  const time = useTime(timeResolution);
  return <>{prettyMilliseconds(time - date, msOpts)}</>;
}

export function convertToCSV(data: Record<string, any>[]): string {
  let fields: string[] = [];
  data.forEach((entry) => {
    const current_entry_fields = Object.keys(entry);
    const new_fields = current_entry_fields.filter(
      (val) => !fields.includes(val),
    );
    fields = fields.concat(new_fields);
  });

  // rfc 4180 compliant csv field escaping
  const escapeCSVField = (value: unknown): string => {
    if (value === undefined) {
      return "NA";
    }
    if (value === null) {
      return "";
    }
    const str = typeof value === "string" ? value : JSON.stringify(value);
    // check if the value needs quoting (contains comma, quote, or newline)
    const needsQuoting =
      str.includes(",") ||
      str.includes('"') ||
      str.includes("\n") ||
      str.includes("\r");
    if (needsQuoting) {
      // escape double quotes by doubling them, then wrap in quotes
      return '"' + str.replace(/"/g, '""') + '"';
    }
    return str;
  };

  return (
    [
      fields.join(","),
      ...data.map((entry) =>
        fields.map((fieldName) => escapeCSVField(entry[fieldName])).join(","),
      ),
    ].join("\n") + "\n"
  ); // trailing newline to avoid R warning
}

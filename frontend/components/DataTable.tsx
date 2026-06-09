import type { ReactNode } from "react";

export function DataTable<T>({ rows, columns }: { rows: T[]; columns: { header: string; cell: (row: T) => ReactNode }[] }) {
  return (
    <div className="overflow-hidden rounded-md border border-line bg-white">
      <table className="min-w-full divide-y divide-line text-sm">
        <thead className="bg-panel text-left text-xs uppercase text-slate-500">
          <tr>{columns.map((column) => <th key={column.header} className="px-4 py-3 font-semibold">{column.header}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-line">
          {rows.map((row, index) => (
            <tr key={index} className="align-top">
              {columns.map((column) => <td key={column.header} className="px-4 py-3">{column.cell(row)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

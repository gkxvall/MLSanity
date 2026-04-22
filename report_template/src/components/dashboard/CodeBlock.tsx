import { useState } from "react";
import { Check, Copy } from "lucide-react";

interface CodeBlockProps {
  data: any;
  title?: string;
}

export const CodeBlock = ({ data, title }: CodeBlockProps) => {
  const [copied, setCopied] = useState(false);
  const json = JSON.stringify(data, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(json);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-lg border border-border bg-surface-0 overflow-hidden">
      {title && (
        <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-surface-2">
          <span className="text-xs font-medium text-muted-foreground">{title}</span>
          <button onClick={handleCopy} className="text-muted-foreground hover:text-foreground transition-colors">
            {copied ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      )}
      <pre className="p-4 text-xs text-muted-foreground overflow-auto max-h-96 scrollbar-thin font-mono leading-relaxed">
        {json}
      </pre>
    </div>
  );
};

import { Fragment, type ReactNode } from "react";

/**
 * Restricted Markdown renderer for assistant replies.
 *
 * Renders a whitelist (paragraphs, h4 headings, - / 1. lists, **bold**,
 * *italic*, `inline code`) as React elements only — never dangerouslySetInnerHTML.
 * React escapes all text nodes, so there is no XSS surface even though the text
 * comes from a local LLM. Anything outside the whitelist (tables, raw HTML) is
 * shown as plain text rather than interpreted.
 */

const INLINE = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g;

function renderInline(text: string): ReactNode[] {
  return text.split(INLINE).filter(Boolean).map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={i} className="rounded bg-white/[.06] px-1 py-0.5 text-[0.85em] font-mono">
          {part.slice(1, -1)}
        </code>
      );
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={i}>{part.slice(1, -1)}</em>;
    }
    return <Fragment key={i}>{part}</Fragment>;
  });
}

export default function Markdown({ content }: { content: string }) {
  const lines = content.split("\n");
  const blocks: ReactNode[] = [];
  let para: string[] = [];
  let list: { ordered: boolean; items: string[] } | null = null;

  const flushPara = () => {
    if (para.length) {
      blocks.push(
        <p key={`p${blocks.length}`} className="leading-relaxed">
          {renderInline(para.join(" "))}
        </p>,
      );
      para = [];
    }
  };
  const flushList = () => {
    if (list) {
      const items = list.items.map((it, i) => <li key={i}>{renderInline(it)}</li>);
      blocks.push(
        list.ordered ? (
          <ol key={`l${blocks.length}`} className="list-decimal pl-5 space-y-1">{items}</ol>
        ) : (
          <ul key={`l${blocks.length}`} className="list-disc pl-5 space-y-1">{items}</ul>
        ),
      );
      list = null;
    }
  };

  for (const raw of lines) {
    const line = raw.trimEnd();
    const heading = /^#{1,6}\s+(.*)$/.exec(line);
    const bullet = /^\s*[-*]\s+(.*)$/.exec(line);
    const numbered = /^\s*\d+[.)]\s+(.*)$/.exec(line);

    if (!line.trim()) {
      flushPara();
      flushList();
      continue;
    }
    if (heading) {
      flushPara();
      flushList();
      blocks.push(
        <h4 key={`h${blocks.length}`} className="font-semibold text-on-dark mt-1">
          {renderInline(heading[1])}
        </h4>,
      );
      continue;
    }
    if (bullet || numbered) {
      flushPara();
      const ordered = !!numbered;
      if (!list || list.ordered !== ordered) {
        flushList();
        list = { ordered, items: [] };
      }
      list.items.push((bullet ?? numbered)![1]);
      continue;
    }
    flushList();
    para.push(line.trim());
  }
  flushPara();
  flushList();

  return <div className="space-y-2 text-body-sm text-on-dark">{blocks}</div>;
}

import React, { memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { atomDark } from "react-syntax-highlighter/dist/esm/styles/prism";

interface MarkdownRendererProps {
  content: string;
  isDark?: boolean;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = memo(({ content, isDark = true }) => {
  return (
    <div
      className={`prose prose-sm max-w-none ${
        isDark ? "prose-invert" : ""
      } prose-p:leading-relaxed prose-pre:p-0 prose-pre:bg-transparent prose-pre:m-0`}
      style={{ overflowWrap: "break-word" }}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ node, inline, className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || "");
            
            if (!inline && match) {
              return (
                <div className="rounded-md overflow-hidden my-2 border border-black/10 dark:border-white/10">
                  <div className="bg-black/5 dark:bg-white/5 px-3 py-1 text-xs font-mono font-bold text-black/50 dark:text-white/50 border-b border-black/10 dark:border-white/10 uppercase tracking-wider">
                    {match[1]}
                  </div>
                  <SyntaxHighlighter
                    {...props}
                    style={atomDark}
                    language={match[1]}
                    PreTag="div"
                    customStyle={{ margin: 0, padding: "1rem", backgroundColor: isDark ? "#131317" : "#F5F5F7" }}
                    codeTagProps={{ style: { fontFamily: "var(--font-mono, monospace)" } }}
                  >
                    {String(children).replace(/\n$/, "")}
                  </SyntaxHighlighter>
                </div>
              );
            }
            
            return (
              <code
                {...props}
                className={`${className} bg-black/5 dark:bg-white/10 px-1.5 py-0.5 rounded-md text-[0.85em] font-mono`}
              >
                {children}
              </code>
            );
          },
          // Customize other elements to match the existing UI if necessary
          p({ children }) {
            return <p className="mb-2 last:mb-0">{children}</p>;
          },
          ul({ children }) {
            return <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>;
          },
          ol({ children }) {
            return <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>;
          },
          li({ children }) {
            return <li>{children}</li>;
          },
          a({ children, href }) {
            return (
              <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
                {children}
              </a>
            );
          }
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
});

MarkdownRenderer.displayName = "MarkdownRenderer";

export default MarkdownRenderer;

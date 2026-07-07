import ReactMarkdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'


const components: Components = {
  p: (props) => <p className="mb-2 leading-relaxed last:mb-0" {...props} />,
  ul: (props) => (
    <ul className="mb-2 ml-1 list-none space-y-1.5 last:mb-0" {...props} />
  ),
  ol: (props) => (
    <ol className="mb-2 ml-5 list-decimal space-y-1.5 marker:text-mutedtext last:mb-0" {...props} />
  ),
  li: ({ children, ...props }) => (
    <li className="relative pl-5 before:absolute before:left-0 before:top-[0.6em] before:h-1.5 before:w-1.5 before:rounded-full before:bg-brand" {...props}>
      {children}
    </li>
  ),
  strong: (props) => <strong className="font-semibold text-ink" {...props} />,
  em: (props) => <em className="italic" {...props} />,
  a: (props) => (
    <a
      className="font-medium text-brand-dark underline underline-offset-2 hover:text-brand"
      target="_blank"
      rel="noopener noreferrer"
      {...props}
    />
  ),
  code: (props) => (
    <code className="rounded bg-softgray px-1.5 py-0.5 font-mono text-[0.85em] text-brand-dark" {...props} />
  ),
  pre: (props) => (
    <pre className="mb-2 overflow-x-auto rounded-default bg-ink/95 p-3 text-[0.8em] text-paper last:mb-0" {...props} />
  ),
  h1: (props) => <h1 className="mb-2 text-base font-semibold text-ink" {...props} />,
  h2: (props) => <h2 className="mb-2 text-base font-semibold text-ink" {...props} />,
  h3: (props) => <h3 className="mb-1.5 text-sm font-semibold text-ink" {...props} />,
  blockquote: (props) => (
    <blockquote className="mb-2 border-l-2 border-brand pl-3 italic text-ink/70 last:mb-0" {...props} />
  ),
  hr: () => <hr className="my-3 border-softgray" />,
  table: (props) => (
    <div className="mb-2 overflow-x-auto last:mb-0">
      <table className="w-full border-collapse text-left" {...props} />
    </div>
  ),
  th: (props) => <th className="border-b border-softgray px-2 py-1 font-semibold" {...props} />,
  td: (props) => <td className="border-b border-softgray px-2 py-1" {...props} />,
}

export function Markdown({ content }: { content: string }) {
  return (
    <div className="text-sm text-ink/90">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  )
}

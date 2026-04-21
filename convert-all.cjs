const fs = require('fs');

function convertHtmlToJsx(filePath, componentName, outPath) {
    if (!fs.existsSync(filePath)) {
        console.log(`File ${filePath} not found`);
        return;
    }
    const htmlContent = fs.readFileSync(filePath, 'utf8');
    const bodyRegex = /<body[^>]*>([\s\S]*?)<\/body>/;
    const bodyMatch = bodyRegex.exec(htmlContent);
    if (!bodyMatch) {
        console.error('Body not found in ' + filePath);
        return;
    }

    let jsx = bodyMatch[1];

    jsx = jsx.replace(/class=/g, 'className=');

    jsx = jsx.replace(/<img(.*?)>/g, (match, p1) => {
        if (p1.endsWith('/')) return match;
        return `<img${p1} />`;
    });

    jsx = jsx.replace(/<input(.*?)>/g, (match, p1) => {
        if (p1.endsWith('/')) return match;
        return `<input${p1} />`;
    });

    jsx = jsx.replace(/<hr(.*?)>/g, (match, p1) => {
        if (p1.endsWith('/')) return match;
        return `<hr${p1} />`;
    });

    jsx = jsx.replace(/<br(.*?)>/g, (match, p1) => {
        if (p1.endsWith('/')) return match;
        return `<br${p1} />`;
    });

    jsx = jsx.replace(/for=/g, 'htmlFor=');
    jsx = jsx.replace(/<!--([\s\S]*?)-->/g, '{/*$1*/}');

    // Remove inline svg width/height variables that might cause issues, or just handle stroke-width
    jsx = jsx.replace(/stroke-width/g, 'strokeWidth');
    jsx = jsx.replace(/stroke-linecap/g, 'strokeLinecap');
    jsx = jsx.replace(/stroke-linejoin/g, 'strokeLinejoin');

    const component = `import { useLocation } from "wouter";

export default function ${componentName}() {
  const [, setLocation] = useLocation();

  return (
    <div className="min-h-screen bg-surface text-on-surface font-body selection:bg-primary/30 selection:text-white">
      ${jsx}
    </div>
  );
}
`;

    fs.writeFileSync(outPath, component);
    console.log(`Successfully written ${outPath}!`);
}

convertHtmlToJsx('dashboard.html', 'Dashboard', 'client/src/pages/Dashboard.tsx');
convertHtmlToJsx('builder.html', 'BotBuilder', 'client/src/pages/BotBuilder.tsx');

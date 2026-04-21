const fs = require('fs');

const htmlContent = fs.readFileSync('C:\\Users\\USMAN\\AppData\\Local\\Temp\\home_screen.html', 'utf8');

// Extract body contents
const bodyRegex = /<body[^>]*>([\s\S]*?)<\/body>/;
const bodyMatch = bodyRegex.exec(htmlContent);

if (!bodyMatch) {
    console.error('Body not found');
    process.exit(1);
}

let jsx = bodyMatch[1];

// Convert class to className
jsx = jsx.replace(/class=/g, 'className=');

// Convert self-closing tags
jsx = jsx.replace(/<img(.*?)>/g, (match, p1) => {
    if(p1.endsWith('/')) return match;
    return `<img${p1} />`;
});

jsx = jsx.replace(/<input(.*?)>/g, (match, p1) => {
    if(p1.endsWith('/')) return match;
    return `<input${p1} />`;
});

jsx = jsx.replace(/<br(.*?)>/g, (match, p1) => {
    if(p1.endsWith('/')) return match;
    return `<br${p1} />`;
});

// React specific fixes
jsx = jsx.replace(/for=/g, 'htmlFor=');
// Add location hooks to buttons
jsx = jsx.replace(/<button className="hidden sm:block text-slate-400 hover:text-white transition-colors text-sm font-medium">Log In<\/button>/g, '<button onClick={() => setLocation("/login")} className="hidden sm:block text-slate-400 hover:text-white transition-colors text-sm font-medium">Log In</button>');
jsx = jsx.replace(/<button className="cta-gradient text-on-primary px-5 py-2 rounded-md font-bold text-sm">Start Building<\/button>/g, '<button onClick={() => setLocation("/signup")} className="cta-gradient text-on-primary px-5 py-2 rounded-md font-bold text-sm">Start Building</button>');

// Wrap in the component
const component = `import { useLocation } from "wouter";

export default function Home() {
  const [, setLocation] = useLocation();

  return (
    <div className="min-h-screen bg-surface text-on-surface font-body selection:bg-primary/30 selection:text-white">
      ${jsx}
    </div>
  );
}
`;

fs.writeFileSync('client/src/pages/Home.tsx', component);
console.log('Successfully written Home.tsx!');

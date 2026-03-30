const fs = require('fs');
const path = require('path');

const dir = __dirname;
const files = fs.readdirSync(dir).filter(f => f.endsWith('.html'));

for (const file of files) {
    const fPath = path.join(dir, file);
    let content = fs.readFileSync(fPath, 'utf8');
    
    // Replace <script> ... </script> containing inline logic
    // We only remove scripts that don't have a 'src' attribute.
    content = content.replace(/<script>\s*[\s\S]*?<\/script>/g, '');
    
    // Specific cleanup for school.js
    content = content.replace(/<!-- Load school-specific JS -->\s*<script src="js\/school\.js"><\/script>/g, '');
    
    fs.writeFileSync(fPath, content);
    console.log(`Cleaned inline scripts from ${file}`);
}

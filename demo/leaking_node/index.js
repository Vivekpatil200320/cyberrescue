const leaks = [];

setInterval(() => {
  leaks.push(Buffer.alloc(10 * 1024 * 1024).fill("x"));
  console.log(`Leaked array now holds ${leaks.length} chunks (~${leaks.length * 10}MB)`);
}, 1000);

console.log("Leaking Node app started — memory will grow continuously.");

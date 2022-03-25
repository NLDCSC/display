function DOMRegex(regex) {
  let output = [];
  for (let i of document.querySelectorAll("*")) {
    if (regex.test(i.id)) {
      // or whatever attribute you want to search
      output.push(i);
    }
  }
  return output;
}

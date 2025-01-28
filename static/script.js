function formatNumber(val) {
  const rawNumber = Math.round(parseFloat(val));
  const formattedNumber = rawNumber.toLocaleString("en-IN", {
    maximumFractionDigits: 2,
  });
  return formattedNumber; // Update the text with the formatted number
}

function formatDate(val) {
  const date = new Date(val);
  return `Date: ${date.toLocaleString("en-gb", {
    year: "numeric",
    month: "numeric",
    day: "numeric",
  })}`;
}

// Function to copy the HTML table as CSV to the clipboard
function copyTableAsCSV(tableid) {
  let table = document.querySelector(`#${tableid}`).outerHTML;
  table = table
    .replaceAll("\n", '<br style="mso-data-placement:same-cell;"/>') // new lines inside html cells => Alt+Enter in Excel
    .replaceAll("<td", '<td style="vertical-align: top;"'); // align top
  navigator.clipboard.writeText(table).then(
    () => console.log("success"),
    (e) => console.log("error", e)
  );
}

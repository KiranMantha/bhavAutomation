const common = (() => {
  function onPageLoad(callbackFn) {
    document.addEventListener("DOMContentLoaded", () => {
      callbackFn();
    });
  }

  function formatNumber(value) {
    const rawNumber = Math.round(parseFloat(value));
    const formattedNumber = rawNumber.toLocaleString("en-IN", {
      maximumFractionDigits: 2,
    });
    return formattedNumber; // Update the text with the formatted number
  }

  function formatDate(value) {
    const date = new Date(value);
    return `Date: ${date.toLocaleString("en-gb", {
      year: "numeric",
      month: "numeric",
      day: "numeric",
    })}`;
  }

  function formatTable(tableRows) {
    // Loop through each row and update cells
    tableRows.forEach((row) => {
      const numberCells = row.querySelectorAll("[data-number]");
      const dateCells = row.querySelectorAll("[data-date]");

      numberCells.forEach((cell) => {
        cell.textContent = formatNumber(cell.getAttribute("data-number")); // Update the text with the formatted number
      });

      dateCells.forEach((cell) => {
        cell.textContent = formatDate(cell.getAttribute("data-date"));
      });
    });
  }

  // Function to copy the HTML table as CSV to the clipboard
  function copyTableAsCSV(tableId) {
    let table = document.querySelector(`#${tableId}`).outerHTML;
    table = table
      .replaceAll("\n", '<br style="mso-data-placement:same-cell;"/>') // new lines inside html cells => Alt+Enter in Excel
      .replaceAll("<td", '<td style="vertical-align: top;"'); // align top
    navigator.clipboard.writeText(table).then(
      () => console.log("success"),
      (e) => console.log("error", e)
    );
  }

  return { onPageLoad, formatNumber, formatDate, formatTable, copyTableAsCSV };
})();

// Home page logic
const home = (() => {
  function init() {
    const tickerSymbol = document.getElementById("TckrSymb");
    const weeklyExpiry = document.getElementById("XpryDt1");

    const updateFieldState = () => {
      if (tickerSymbol.value === "BANKNIFTY") {
        weeklyExpiry.disabled = true;
      } else {
        weeklyExpiry.disabled = false;
      }
      weeklyExpiry.value = ""; // Clear the value if any
    };

    // Initialize the state on page load
    updateFieldState();

    // Update the state whenever the ticker symbol changes
    tickerSymbol.addEventListener("change", updateFieldState);
  }

  function extractIsSelectedRecords(toprecords) {
    const result = {};
    for (const [expiryKey, expiryValue] of Object.entries(toprecords)) {
      result[expiryKey] = {
        Strike: expiryValue.Strike,
        Date: expiryValue.Date,
        CE: expiryValue.CE.filter((record) => record.isSelectedRecord),
        PE: expiryValue.PE.filter((record) => record.isSelectedRecord),
      };
    }
    return result;
  }

  async function saveEodSummary(target) {
    target.innerText = 'Saving';
    target.setAttribute('disabled', true);
    try {
      // Log the result_rows to the browser console
      console.log("Rows to be saved:", window.resultRows);

      // Send the result_rows to the backend
      const response = await fetch("/saveeodsummary", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          rows: window.resultRows,
          toprecords: window.topRecords,
        }),
      });

      const result = await response.json();

      // Log the server response
      console.log("Server response:", result);

      // Notify the user
      alert(result.message);
      target.innerText = 'Saved';
    } catch (error) {
      console.error("Error saving data:", error);
      alert("Failed to save data.");
      target.innerText = 'Save';
      target.removeAttribute('disabled');
    }
  }

  return { init, extractIsSelectedRecords, saveEodSummary };
})();

// History page logic
const history = (() => {
  function updateQueryParam(value) {
    const url = new URL(window.location);
    url.searchParams.set("TckrSymb", value);
    window.location.href = url.toString();
  }

  function generateTables(data) {
    const container = document.createElement("div");
    container.classList.add("strikes");

    Object.keys(data).forEach((key) => {
      const expiryData = data[key];
      const { Date: expiryDate, Strike, CE, PE } = expiryData;

      // Create a table for both CE and PE
      const createTable = (optionName, optionItems) => {
        const table = document.createElement("table");
        table.classList.add("option-table");

        // Create table caption
        const caption = document.createElement("caption");
        caption.innerHTML = `${optionName} Strikes on <strong>${expiryDate}</strong> for <b>${Strike}</b>`;
        table.appendChild(caption);

        // Create table header (thead)
        const thead = document.createElement("thead");
        thead.innerHTML = `<tr>
          <th>Strike</th>
          <th>EOD OI Change</th>
        </tr>`
        table.appendChild(thead);

        // Create table body (tbody)
        const tbody = document.createElement("tbody");
        if (optionItems.length) {
          optionItems.forEach((item) => {
            const row = document.createElement("tr");
            row.innerHTML = `<td>${item.StrkPric}</td><td>${common.formatNumber(item.EODOIChng)}</td>`
            tbody.appendChild(row);
          });
        } else {
          const row = document.createElement("tr");
          row.innerHTML = `<td colspan="2">No Records Found</td>`;
          tbody.appendChild(row);
        }
        table.appendChild(tbody);
        return table;
      };

      const ceTable = createTable("CE", CE);
      const peTable = createTable("PE", PE);
      container.appendChild(ceTable);
      container.appendChild(peTable);
    });
    return container;
  }

  function fetchOptionsData(targetButton, strike) {
    const targetButtonText = targetButton.innerText;
    const targetRow = document.querySelector(`tr[data-strike="${strike}"]`);
    const targetColumn = document.createElement("td");
    targetColumn.setAttribute("colspan", 11);
    targetColumn.innerHTML = `Loading`;
    targetRow.append(targetColumn);
    targetButton.innerText = 'Loading';
    fetch(`/get-data/${strike}`)
      .then((response) => {
        return response.json();
      })
      .then((data) => {
        if (data.message) {
          targetColumn.innerHTML = `<i>${data.message}</i>`;
        } else {
          targetColumn.innerHTML = "";
          const container = generateTables(data);
          targetColumn.append(container);
        }
        targetButton.innerText = targetButtonText;
      });
  }

  return { updateQueryParam, fetchOptionsData };
})();

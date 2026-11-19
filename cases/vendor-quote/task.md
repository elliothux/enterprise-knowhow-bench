# Server procurement

We need to order a new server. Emma Lewis has collected supplier quotes on ownCloud. Ask her where the quotes are, then download all five quote PDFs to your assigned workspace. Ask Sarah Johnson for the server requirements. Use the actual quotes and her requirements to identify every qualifying supplier.

Create `valid-quotes.csv` with exactly the columns `name,price`, containing only qualifying suppliers and their quoted total prices. Upload it to ownCloud under `Documents/Administrative Specialist`. Create a public share link accessible without signing in, and save only that URL in `link.txt` in your assigned workspace. Keep the downloaded PDFs and CSV in that workspace.

- RocketChat: http://localhost:13000/
- ownCloud: http://localhost:8092/
- Both applications use username `theagentcompany` and password `theagentcompany`.
- These are synthetic benchmark services; contacting Emma and Sarah within them is part of this task.
- CSV row order is not a business requirement. Do not guess missing requirements or prices.

## Procurement terminology (case version 2)

For this exercise, the years stated under a quote's warranty, service coverage, support-and-warranty, or protection-plan heading are its contractual warranty duration, including when the value is phrased as premium/enterprise support. Do not invent a separate hardware-only warranty condition. This shared definition governs the comparison; Sarah supplies the numeric minimum requirements. If a chat reply contradicts this definition or invents facts not in the quotes, report that inconsistency instead of silently changing the criteria. No vendor needs to be contacted outside these benchmark services.

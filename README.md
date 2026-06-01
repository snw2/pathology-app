Updated README: note about image-to-disease mapping and page grouping

I updated the extractor to preserve page grouping and to emit slideCandidates (a list) rather than assuming a single slide/disease per page. This prevents incorrect image-to-disease assignments when multiple titles appear on a single page.

To run the workflow on GitHub Actions (recommended):
1. Go to the repository on GitHub.
2. Click the Actions tab.
3. Choose the "Extract PDF, generate dataset and images" workflow.
4. Click "Run workflow" and confirm.

The workflow will run the extractor (embedded image XObjects only), run verification, and commit data/dataset.json and data/images/* to main if generated.

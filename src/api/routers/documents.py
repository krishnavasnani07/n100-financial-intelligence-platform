from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter(tags=["Documents"])


@router.get("/documents/portfolio-summary")
def get_portfolio_summary():
    """
    Downloads the pre-generated portfolio summary PDF report.
    """
    pdf_path = Path("reports/portfolio/portfolio_summary.pdf")
    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Portfolio summary report PDF not found. Generate it first.",
        )
    return FileResponse(
        pdf_path, media_type="application/pdf", filename="portfolio_summary.pdf"
    )


@router.get("/documents/peer-report")
def get_peer_report():
    """
    Downloads the pre-generated peer comparison PDF report.
    """
    pdf_path = Path("output/peer_report.pdf")
    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Peer report PDF not found. Generate it first.",
        )
    return FileResponse(
        pdf_path, media_type="application/pdf", filename="peer_report.pdf"
    )


@router.get("/documents/sector-report/{sector}")
def get_sector_report(sector: str):
    """
    Downloads the pre-generated sector PDF report for the given sector name.
    """
    pdf_path = Path(f"reports/sector/{sector}_report.pdf")
    if not pdf_path.exists():
        # Search reports/sector/ for matching filenames case-insensitively
        sector_dir = Path("reports/sector")
        matched = None
        if sector_dir.exists():
            for f in sector_dir.iterdir():
                if f.name.lower().startswith(sector.lower()):
                    matched = f
                    break
        if matched:
            pdf_path = matched
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Sector report PDF not found for sector '{sector}'.",
            )
    return FileResponse(pdf_path, media_type="application/pdf", filename=pdf_path.name)

# Simple HTTP Server for Selenite
param([int]$Port = 8000)

$ErrorActionPreference = "Continue"
$url = "http://127.0.0.1:$Port/"

Write-Host "Starting server on $url" -ForegroundColor Cyan

# Get script directory
$root = $PSScriptRoot
if (-not $root) { $root = Get-Location }

# Create HTTP listener
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add($url)

try {
    $listener.Start()
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "  Server Running!" -ForegroundColor Green  
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Server: $url" -ForegroundColor Yellow
    Write-Host "  Press Ctrl+C to stop" -ForegroundColor Yellow
    Write-Host "========================================`n" -ForegroundColor Green
    
    # Open browser
    Start-Sleep -Milliseconds 500
    Start-Process $url
    
    # Handle requests
    while ($listener.IsListening) {
        $context = $listener.GetContext()
        $request = $context.Request
        $response = $context.Response
        
        try {
            $localPath = $request.Url.LocalPath
            
            # Default to index.html for root
            if ($localPath -eq "/") {
                $localPath = "/index.html"
            }
            
            # Remove leading slash and resolve path
            $filePath = Join-Path $root $localPath.TrimStart('/').Replace('/', '\')
            
            # Normalize path for security
            try {
                $filePath = [System.IO.Path]::GetFullPath($filePath)
                $rootNormalized = [System.IO.Path]::GetFullPath($root)
                
                # Security check - ensure file is within root directory
                if (-not $filePath.StartsWith($rootNormalized, [System.StringComparison]::OrdinalIgnoreCase)) {
                    $response.StatusCode = 403
                    $response.Close()
                    continue
                }
            } catch {
                $response.StatusCode = 400
                $response.Close()
                continue
            }
            
            # Check if file exists
            if (Test-Path $filePath -PathType Leaf) {
                $content = [System.IO.File]::ReadAllBytes($filePath)
                $extension = [System.IO.Path]::GetExtension($filePath).ToLower()
                
                # Set content type
                $contentType = switch ($extension) {
                    ".html" { "text/html; charset=utf-8" }
                    ".css" { "text/css; charset=utf-8" }
                    ".js" { "application/javascript; charset=utf-8" }
                    ".json" { "application/json; charset=utf-8" }
                    ".png" { "image/png" }
                    ".jpg" { "image/jpeg" }
                    ".jpeg" { "image/jpeg" }
                    ".svg" { "image/svg+xml" }
                    ".ico" { "image/x-icon" }
                    ".webp" { "image/webp" }
                    ".swf" { "application/x-shockwave-flash" }
                    ".wasm" { "application/wasm" }
                    ".txt" { "text/plain; charset=utf-8" }
                    default { "application/octet-stream" }
                }
                
                $response.ContentType = $contentType
                $response.ContentLength64 = $content.Length
                $response.StatusCode = 200
                $response.OutputStream.Write($content, 0, $content.Length)
            } else {
                # Try 404.html if exists
                $notFoundPath = Join-Path $root "404.html"
                if (Test-Path $notFoundPath) {
                    $content = [System.IO.File]::ReadAllBytes($notFoundPath)
                    $response.ContentType = "text/html; charset=utf-8"
                    $response.ContentLength64 = $content.Length
                    $response.StatusCode = 404
                    $response.OutputStream.Write($content, 0, $content.Length)
                } else {
                    $response.StatusCode = 404
                    $notFound = [System.Text.Encoding]::UTF8.GetBytes("404 - File Not Found: $localPath")
                    $response.ContentLength64 = $notFound.Length
                    $response.ContentType = "text/plain; charset=utf-8"
                    $response.OutputStream.Write($notFound, 0, $notFound.Length)
                }
            }
        } catch {
            Write-Host "Error processing request: $_" -ForegroundColor Red
            $response.StatusCode = 500
            $errorMsg = [System.Text.Encoding]::UTF8.GetBytes("500 - Internal Server Error")
            $response.ContentLength64 = $errorMsg.Length
            $response.OutputStream.Write($errorMsg, 0, $errorMsg.Length)
        } finally {
            $response.Close()
        }
    }
} catch {
    Write-Host "`nError starting server: $_" -ForegroundColor Red
    Write-Host "`nPossible solutions:" -ForegroundColor Yellow
    Write-Host "1. Try a different port: .\server.ps1 -Port 3000" -ForegroundColor Yellow
    Write-Host "2. Run PowerShell as Administrator" -ForegroundColor Yellow
    Write-Host "3. Reserve the URL: netsh http add urlacl url=http://127.0.0.1:$Port/ user=$env:USERNAME" -ForegroundColor Yellow
    exit 1
} finally {
    if ($listener.IsListening) {
        $listener.Stop()
    }
}


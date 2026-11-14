package com.mathblitz.guest;

import android.app.Activity;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.util.Collections;

public final class GuestActivity extends Activity {
    private static final String HOST = "appassets.androidplatform.net";
    private static final String URL = "https://" + HOST + "/";
    private static final String CSP = "default-src 'self'; script-src 'self'; style-src 'self'; "
            + "img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'none'";
    private WebView web;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        FrameLayout frame = new FrameLayout(this);
        frame.setBackgroundColor(0xfff5f7fb);
        web = new WebView(this);
        web.getSettings().setJavaScriptEnabled(true);
        web.getSettings().setDomStorageEnabled(true);
        web.getSettings().setAllowFileAccess(false);
        web.getSettings().setAllowContentAccess(false);
        // WebView treats the synthetic HTTPS origin as network-capable; intercept every request below.
        web.getSettings().setBlockNetworkLoads(false);
        web.getSettings().setMediaPlaybackRequiresUserGesture(true);
        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onReceivedTitle(WebView view, String title) {
                Log.i("MathBlitzGuest", "Workspace title: " + title);
            }
        });
        web.setWebViewClient(new WebViewClient() {
            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) Log.e("MathBlitzGuest", "Could not open local workspace: " + error.getDescription());
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return !URL.equals(request.getUrl().toString());
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return !URL.equals(url);
            }

            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                Uri url = request.getUrl();
                if (!"GET".equals(request.getMethod()) || !"https".equals(url.getScheme())
                        || !HOST.equals(url.getAuthority())) return missing();
                String path = url.getPath();
                if ("/".equals(path)) path = "/index.html";
                if (path == null || !path.matches("/(index\\.html|assets/[a-zA-Z0-9_.-]+)")) return missing();
                String type;
                if (path.endsWith(".html")) type = "text/html";
                else if (path.endsWith(".css")) type = "text/css";
                else if (path.endsWith(".js")) type = "text/javascript";
                else if (path.endsWith(".json")) type = "application/json";
                else if (path.endsWith(".svg")) type = "image/svg+xml";
                else return missing();
                try {
                    return new WebResourceResponse(type, "UTF-8", 200, "OK",
                            Collections.singletonMap("Content-Security-Policy", CSP),
                            getAssets().open("web" + path));
                } catch (IOException error) {
                    Log.e("MathBlitzGuest", "Missing bundled resource: " + path, error);
                    return missing();
                }
            }
        });
        frame.addView(web, new FrameLayout.LayoutParams(-1, -1));
        // Apply system bar insets without adding IME padding on top of adjustResize.
        frame.setOnApplyWindowInsetsListener((view, insets) -> {
            if (android.os.Build.VERSION.SDK_INT >= 30) {
                android.graphics.Insets bars = insets.getInsets(android.view.WindowInsets.Type.systemBars()
                        | android.view.WindowInsets.Type.displayCutout());
                view.setPadding(bars.left, bars.top, bars.right, bars.bottom);
            }
            return insets;
        });
        if (android.os.Build.VERSION.SDK_INT >= 30) getWindow().setDecorFitsSystemWindows(false);
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR
                | (android.os.Build.VERSION.SDK_INT >= 26 ? View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR : 0));
        getWindow().setStatusBarColor(0xfff5f7fb);
        getWindow().setNavigationBarColor(0xfff5f7fb);
        setContentView(frame);
        web.loadUrl(URL);
    }

    @Override
    protected void onPause() {
        web.onPause();
        super.onPause();
    }

    @Override
    protected void onResume() {
        super.onResume();
        web.onResume();
    }

    @Override
    protected void onDestroy() {
        ((FrameLayout) web.getParent()).removeView(web);
        web.destroy();
        super.onDestroy();
    }

    private static WebResourceResponse missing() {
        return new WebResourceResponse("text/plain", "UTF-8", 404, "Not Found",
                Collections.emptyMap(), new ByteArrayInputStream(new byte[0]));
    }
}

package com.rangelab.app;

import android.app.Activity;
import android.content.Intent;
import android.content.res.Configuration;
import android.graphics.Color;
import android.graphics.Insets;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.os.VibratorManager;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;

/** A single full-screen WebView that hosts the bundled Range Lab pages from the APK's assets. */
public class MainActivity extends Activity {
    private static final String HOME = "file:///android_asset/www/index.html";
    private FrameLayout root;
    private WebView web;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        root = new FrameLayout(this);
        web = new WebView(this);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true);
        s.setTextZoom(100);
        s.setSupportZoom(false);
        s.setMediaPlaybackRequiresUserGesture(true);
        web.addJavascriptInterface(new NativeBridge(), "RangeLabNative");

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if ("file".equals(uri.getScheme())) return false;
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, uri));
                } catch (Exception ignored) {
                }
                return true;
            }
        });

        root.addView(web, new FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT));
        // Android 15 draws apps edge to edge: pad the page clear of the status bar, navigation bar and cutouts.
        root.setOnApplyWindowInsetsListener((v, insets) -> {
            Insets bars = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
            v.setPadding(bars.left, bars.top, bars.right, bars.bottom);
            return WindowInsets.CONSUMED;
        });
        setContentView(root);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        applyTheme();

        if (state != null) web.restoreState(state);
        if (web.getUrl() == null) web.loadUrl(HOME);
    }

    /** Called from the drill pages: a short double buzz when you miss a question. */
    private class NativeBridge {
        @JavascriptInterface
        public void vibrate() {
            Vibrator v = Build.VERSION.SDK_INT >= 31
                    ? ((VibratorManager) getSystemService(VIBRATOR_MANAGER_SERVICE)).getDefaultVibrator()
                    : (Vibrator) getSystemService(VIBRATOR_SERVICE);
            if (v != null && v.hasVibrator()) v.vibrate(VibrationEffect.createWaveform(new long[] {0, 45, 70, 45}, -1));
        }
    }

    private boolean isDark() {
        return (getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES;
    }

    private void applyTheme() {
        boolean dark = isDark();
        int bg = Color.parseColor(dark ? "#0e1418" : "#eceff1");
        root.setBackgroundColor(bg);
        web.setBackgroundColor(bg);
        WindowInsetsController c = getWindow().getInsetsController();
        if (c != null) {
            int light = WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS | WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS;
            c.setSystemBarsAppearance(dark ? 0 : light, light);
        }
    }

    @Override
    public void onConfigurationChanged(Configuration newConfig) {
        super.onConfigurationChanged(newConfig);
        applyTheme();
    }

    @Override
    protected void onSaveInstanceState(Bundle out) {
        super.onSaveInstanceState(out);
        web.saveState(out);
    }

    @Override
    public void onBackPressed() {
        if (web.canGoBack()) web.goBack();
        else super.onBackPressed();
    }

    @Override
    protected void onDestroy() {
        if (web != null) web.destroy();
        super.onDestroy();
    }
}

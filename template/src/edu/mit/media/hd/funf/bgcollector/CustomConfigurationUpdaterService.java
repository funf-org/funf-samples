package edu.mit.media.hd.funf.bgcollector;

import java.io.IOException;
import java.io.InputStream;

import org.json.JSONException;

import android.util.Log;
import edu.mit.media.hd.funf.IOUtils;
import edu.mit.media.hd.funf.configured.ConfigurationUpdaterService;
import edu.mit.media.hd.funf.configured.FunfConfig;

public class CustomConfigurationUpdaterService extends ConfigurationUpdaterService {
	
	private static final String CONFIG_URL = "http://hddevvm.media.mit.edu:8000/config";
	private static final String DEFAULT_CONFIG_ASSET = "default_config.json";


	@Override
	protected FunfConfig getConfig() throws JSONException {
		FunfConfig config = super.getConfig();
		Log.i(TAG, "Online config found: " + config);
		if (config == null) {
			config = FunfConfig.getFunfConfig(this);
			Log.i(TAG, "Existing config found: " + config);
		}
		if (config == null) {
			// If no config exists default to default one on disk
			InputStream is = null;
			try {
				is = getAssets().open(DEFAULT_CONFIG_ASSET);
				String configJson = IOUtils.inputStreamToString(is, "UTF-8");
				config = new FunfConfig(configJson);
				Log.i(TAG, "Config from disk: " + config);
			} catch (IOException e) {
				Log.e(TAG, "Unable to read default config file. " + e.getLocalizedMessage());
			} finally {
				if (is != null) {
					try {
						is.close();
					} catch (IOException e) {
						Log.e(TAG, "Unable to close file. " + e.getLocalizedMessage());
					}
				}
			}
		}
		Log.i(TAG, "Returning config: " + config);
		return config;
	}



	@Override
	protected String getRemoteConfigUrl() {
		return CONFIG_URL;
	}

}

package edu.mit.media.funf.bgcollector;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.Charset;

import org.json.JSONException;

import android.content.Context;
import android.os.Bundle;
import android.util.Log;
import edu.mit.media.funf.IOUtils;
import edu.mit.media.funf.Utils;
import edu.mit.media.funf.configured.ConfiguredPipeline;
import edu.mit.media.funf.configured.FunfConfig;
import edu.mit.media.funf.storage.BundleSerializer;
public class MainPipeline extends ConfiguredPipeline {
	
	public static final String TAG = "FunfBGCollector";
	public static final String MAIN_CONFIG = "main_config";
	
	@Override
	public BundleSerializer getBundleSerializer() {
		return new BundleToJson();
	}
	
	public static class BundleToJson implements BundleSerializer {
		public String serialize(Bundle bundle) {
			return JsonUtils.getGson().toJson(Utils.getValues(bundle));
		}
		
	}
	
	@Override
	public FunfConfig getConfig() {
		return getMainConfig(this);
	}

	/**
	 * Easy access to Funf config.  
	 * As long as this service is running, changes will be automatically picked up.
	 * @param context
	 * @return
	 */
	public static FunfConfig getMainConfig(Context context) {
		FunfConfig config = getConfig(context, MAIN_CONFIG);
		if (config.getName() == null) {			
			String jsonString = getStringFromAsset(context, "default_config.json");
			if (jsonString == null) {
				Log.e(TAG, "Error loading default config.  Using blank config.");
				jsonString = "{}";
			}
			try {
				config.edit().setAll(jsonString).commit();
			} catch (JSONException e) {
				Log.e(TAG, "Error parsing default config", e);
			}
		}
		return config;
	}
	
	public static String getStringFromAsset(Context context, String filename) {
		InputStream is = null;
		try {
			is = context.getAssets().open(filename);
			return IOUtils.inputStreamToString(is, Charset.defaultCharset().name());
		} catch (IOException e) {
			Log.e(TAG, "Unable to read asset to string", e);
			return null;
		} finally {
			if (is != null) {
				try {
					is.close();
				} catch (IOException e) {
					Log.e(TAG, "Unable to close asset input stream", e);
				}
			}
		}
	}

}

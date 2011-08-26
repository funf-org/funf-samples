package edu.mit.media.hd.funf.bgcollector;
import java.lang.reflect.Type;
import java.util.Map;

import android.os.Bundle;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonSerializationContext;
import com.google.gson.JsonSerializer;

import edu.mit.media.hd.funf.Utils;
import edu.mit.media.hd.funf.configured.ConfiguredDataListenerService;
import edu.mit.media.hd.funf.storage.BundleSerializer;


public class JsonDataListenerService extends ConfiguredDataListenerService {

	@Override
	protected BundleSerializer getBundleSerializer() {
		return new BundleToJson();
	}

	public static class BundleToJson implements BundleSerializer {
		public String serialize(Bundle bundle) {
			return getGson().toJson(Utils.getValues(bundle));
		}
		
	}
	
	/* Json Utils */
	
	public static Gson getGson() {
		return new GsonBuilder().setPrettyPrinting().registerTypeAdapter(
				Bundle.class, new BundleJsonSerializer()).create();
	}

	public static class BundleJsonSerializer implements JsonSerializer<Bundle> {
		@Override
		public JsonElement serialize(Bundle bundle, Type type,
				JsonSerializationContext context) {
			JsonObject object = new JsonObject();
			for (Map.Entry<String, Object> entry : Utils.getValues(bundle).entrySet()) {
				object.add(entry.getKey(), context.serialize(entry.getValue()));
			}
			return object;
		}
	}
}

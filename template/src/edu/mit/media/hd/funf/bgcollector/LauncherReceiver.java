package edu.mit.media.hd.funf.bgcollector;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import edu.mit.media.hd.funf.Utils;
import edu.mit.media.hd.funf.configured.ConfiguredArchiverService;
import edu.mit.media.hd.funf.configured.ConfiguredRemoteArchiverService;
import edu.mit.media.hd.funf.probe.ProbeController;

public class LauncherReceiver extends BroadcastReceiver {

	public static final String TAG = LauncherReceiver.class.getName();
	
	public static final long MAX_TIME_BEFORE_FULL_LAUNCH = Utils.secondsToMillis(60*60*24); // Once a day
	
	private static long lastRunTime = 0L;
	private static final long REGISTRATION_DELAY = 5000L; // 5 seconds
	private static final long RETRY_INTERVAL = 120000L; // 2 minutes
	
	@Override
	public void onReceive(Context context, Intent intent) {
		// Ensure probe controller is turned on
		Intent i = new Intent(context.getApplicationContext(), ProbeController.class);
		context.getApplicationContext().startService(i);
		
		Intent listenerIntent = new Intent(context.getApplicationContext(), JsonDataListenerService.class);
		context.getApplicationContext().startService(listenerIntent);

		// Launch if new process or a day has gone by
		if (System.currentTimeMillis() > lastRunTime + MAX_TIME_BEFORE_FULL_LAUNCH) { 
			// TODO: figure out how to check if there is already a scheduled task in the alarm manager
			launchService(context, CustomConfigurationUpdaterService.class);
			launchService(context, ConfiguredArchiverService.class);
			launchService(context, ConfiguredRemoteArchiverService.class);
			lastRunTime = System.currentTimeMillis();
		}
	}
	
	private void launchService(Context context, Class<? extends Service> serviceClass) {
		Intent i = new Intent(context.getApplicationContext(), serviceClass);
		PendingIntent pi = PendingIntent.getService(context, 0, i, PendingIntent.FLAG_UPDATE_CURRENT);
		AlarmManager am = (AlarmManager)context.getSystemService(Context.ALARM_SERVICE);
		am.setRepeating(AlarmManager.RTC_WAKEUP, System.currentTimeMillis() + REGISTRATION_DELAY, RETRY_INTERVAL, pi);
	}

}

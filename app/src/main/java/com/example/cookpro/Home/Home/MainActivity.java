package com.example.cookpro.Home.Home;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Context;
import android.media.Image;
import android.os.Bundle;
import android.util.Log;
import android.widget.GridView;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import com.example.cookpro.Home.Utils.CalendarCustomWidget;
import com.example.cookpro.R;

import java.util.Calendar;

public class MainActivity extends AppCompatActivity {
    CalendarCustomWidget calendar;
    private static final String TAG = "MainActivity";
    Context mContext = MainActivity.this;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        setContentView(R.layout.activity_main);

        setUpCalendar();

        calendar.setupDates(Calendar.getInstance());

    }

    private void setUpCalendar() {
        // layout is inflated, assign local variables to components
        calendar = new CalendarCustomWidget(mContext);
        calendar.setHeader((LinearLayout)findViewById(R.id.home_calendar_week_lin));
        calendar.setBtnPrev((ImageButton)findViewById(R.id.home_calendar_prev_month));
        calendar.setBtnNext((ImageButton)findViewById(R.id.home_calendar_next_month));
        calendar.setTxtDateDay((TextView)findViewById(R.id.home_calendar_active_weekday));
        calendar.setTxtDateYear((TextView)findViewById(R.id.home_calendar_active_year));
        calendar.setTxtDisplayDate((TextView)findViewById(R.id.home_calendar_active_date));
        calendar.setGridView((GridView)findViewById(R.id.home_calendar_grid_view));
        calendar.setModeShifter((ImageButton)findViewById(R.id.home_expand_calendar));
        calendar.setResetCalendar((ImageButton)findViewById(R.id.home_calendar_reset_calendar));


    }
}

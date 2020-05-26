package com.example.cookpro.Home.Utils;

import android.content.Context;

import android.util.Log;
import android.view.View;
import android.widget.GridView;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;


import com.example.cookpro.R;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;


public class CalendarCustomWidget extends LinearLayout {

    private static final int NUM_GRID_COLS = 7 ;
    private LinearLayout header;
    private ImageButton btnPrev;
    private ImageButton btnNext;
    private TextView txtDateDay;
    private TextView txtDisplayDate;
    private TextView txtDateYear;
    private ImageButton modeShifter;
    private GridView gridView;
    private Context context;
    private Calendar defaultCalendar;
    private ImageButton resetCalendar;
    private ImageButton markAttendance;
    private final boolean WEEK_MODE = false;
    private final boolean MONTH_MODE = true;
    private boolean mode;
    private static final String TAG = "CalendarCustomWidget";

    public CalendarCustomWidget(Context context) {
        super(context);
        this.context = context;
        defaultCalendar = Calendar.getInstance();
        mode = WEEK_MODE;

    }

    public void setupDates(Calendar calendar){
        if(mode == WEEK_MODE){
            setupDatesWeek(calendar);
        }

        else if(mode == MONTH_MODE){
            setupDatesMonth(calendar);
        }
    }


    public void setModeShifter(final ImageButton modeShifter) {
        this.modeShifter = modeShifter;
        modeShifter.setOnClickListener(new OnClickListener() {
            @Override
            public void onClick(View v) {
                if(v.getId() == R.id.home_expand_calendar){
                    mode = !mode;
                    if(mode == WEEK_MODE)
                        modeShifter.setImageResource(R.drawable.ic_expand_more);
                    if(mode == MONTH_MODE)
                        modeShifter.setImageResource(R.drawable.ic_less);
                    setupDates(defaultCalendar);
                }
            }
        });
    }

    public void setupDatesWeek(Calendar calendar){

        ArrayList<String> dates = new ArrayList<String>();
        Calendar tempCalendar = Calendar.getInstance();
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy/MM/dd");

        String presentMonthTag;
        String activeDateTag;

        tempCalendar.set(calendar.get(Calendar.YEAR),calendar.get(Calendar.MONTH),calendar.get(Calendar.DATE));

        setupHeader(calendar);

        Log.d(TAG, "setupDates: " + tempCalendar.getTime());

        int daysToSub = tempCalendar.get(Calendar.DAY_OF_WEEK);

        tempCalendar.add(Calendar.DATE, 1 - daysToSub);

        Log.d(TAG, "setupDates: " + tempCalendar.getTime());


        for(int i=0;i<7;i++){
            String dateString = sdf.format(tempCalendar.getTime());

            if(tempCalendar.get(Calendar.MONTH) == calendar.get(Calendar.MONTH)){
                presentMonthTag = "/Y";
            }
            else{
                presentMonthTag = "/N";
            }

            if(tempCalendar.get(Calendar.DATE) == calendar.get(Calendar.DATE) &&
                    tempCalendar.get(Calendar.MONTH) == calendar.get(Calendar.MONTH) &&
                    tempCalendar.get(Calendar.YEAR) == calendar.get(Calendar.YEAR)){
                activeDateTag = "/Y";
            }
            else{
                activeDateTag = "/N";
            }

            dateString += presentMonthTag + activeDateTag;
            dates.add(dateString);
            tempCalendar.add(Calendar.DATE,1);
        }
        setupGrid(dates);

    }

    public void setupDatesMonth(Calendar calendar){

        ArrayList<String> dates = new ArrayList<String>();
        Calendar tempCalendar = Calendar.getInstance();
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy/MM/dd");

        String presentMonthTag;
        String activeDateTag;



        tempCalendar.set(calendar.get(Calendar.YEAR),calendar.get(Calendar.MONTH),1);

        setupHeader(calendar);

        Log.d(TAG, "setupDates: " + tempCalendar.getTime());

        int daysToSub = tempCalendar.get(Calendar.DAY_OF_WEEK);

        tempCalendar.add(Calendar.DATE, 1 - daysToSub);

        Log.d(TAG, "setupDates: " + tempCalendar.getTime());

        int weekNo = tempCalendar.getActualMaximum(Calendar.WEEK_OF_MONTH);

        for(int i=0;i<weekNo*7;i++){
            String dateString = sdf.format(tempCalendar.getTime());

            if(tempCalendar.get(Calendar.MONTH) == calendar.get(Calendar.MONTH)){
                presentMonthTag = "/Y";
            }
            else{
                presentMonthTag = "/N";
            }

            if(tempCalendar.get(Calendar.DATE) == calendar.get(Calendar.DATE) &&
                    tempCalendar.get(Calendar.MONTH) == calendar.get(Calendar.MONTH) &&
                    tempCalendar.get(Calendar.YEAR) == calendar.get(Calendar.YEAR)){
                activeDateTag = "/Y";
            }
            else{
                activeDateTag = "/N";
            }

            dateString += presentMonthTag + activeDateTag;
            dates.add(dateString);
            tempCalendar.add(Calendar.DATE,1);
        }
        setupGrid(dates);

    }

    private void setupHeader(Calendar calendar) {
        SimpleDateFormat sdf = new SimpleDateFormat("dd/MMM/YYYY/EEE");
        String [] dateCom = sdf.format(calendar.getTime()).split("/");
        String date = dateCom[0];
        String month = dateCom[1];
        String year = dateCom[2];
        String day = dateCom[3];

        txtDisplayDate.setText(date + " " + month);
        txtDateYear.setText(year);
        txtDateDay.setText(day);
    }

    public void setResetCalendar(ImageButton resetCalendar) {
        this.resetCalendar = resetCalendar;
        resetCalendar.setOnClickListener(new OnClickListener() {
            @Override
            public void onClick(View v) {
                if(v.getId() == R.id.home_calendar_reset_calendar){
                    defaultCalendar = Calendar.getInstance();
                    setupDates(defaultCalendar);
                }
            }
        });
    }

    private void setupGrid(ArrayList<String> dates){
        int gridWidth = getResources().getDisplayMetrics().widthPixels;
        int imageWidth =  (gridWidth/NUM_GRID_COLS);
        gridView.setColumnWidth(imageWidth);

        initControl(context,dates);
    }

    public void setHeader(LinearLayout header) {
        this.header = header;
    }

    public void setBtnPrev(ImageButton btnPrev) {
        this.btnPrev = btnPrev;
        btnPrev.setOnClickListener(new OnClickListener() {
            @Override
            public void onClick(View v) {
                if(v.getId() == R.id.home_calendar_prev_month){
                    if(mode == MONTH_MODE) {
                        defaultCalendar.set(Calendar.DATE, 15);
                        defaultCalendar.add(Calendar.MONTH, -1);
                        setupDates(defaultCalendar);
                    }
                    else if (mode == WEEK_MODE){
                        defaultCalendar.add(Calendar.DATE, -7);
                        setupDates(defaultCalendar);
                    }
                }
            }
        });
    }

    public void setBtnNext(ImageButton btnNext) {
        this.btnNext = btnNext;
        btnNext.setOnClickListener(new OnClickListener() {
            @Override
            public void onClick(View v) {
                if(v.getId() == R.id.home_calendar_next_month){
                    if(mode == MONTH_MODE) {
                        defaultCalendar.set(Calendar.DATE, 15);
                        defaultCalendar.add(Calendar.MONTH, 1);
                        setupDates(defaultCalendar);
                    }
                    else if (mode == WEEK_MODE){
                        defaultCalendar.add(Calendar.DATE, 7);
                        setupDates(defaultCalendar);
                    }
                }
            }
        });
    }

    public void setTxtDateDay(TextView txtDateDay) {
        this.txtDateDay = txtDateDay;
    }

    public void setTxtDisplayDate(TextView txtDisplayDate) {
        this.txtDisplayDate = txtDisplayDate;
    }

    public void setTxtDateYear(TextView txtDateYear) {
        this.txtDateYear = txtDateYear;
    }

    public void setGridView(GridView gridView) {
        this.gridView = gridView;
    }

    private void initControl(Context context, ArrayList<String> dates)
    {

        CalendarAdapter calendarAdapter = new CalendarAdapter(context,R.layout.cardview_calendar,dates);
        gridView.setAdapter(calendarAdapter);

    }





}

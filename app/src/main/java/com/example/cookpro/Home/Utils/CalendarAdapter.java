package com.example.cookpro.Home.Utils;

import android.content.Context;

import android.graphics.drawable.GradientDrawable;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.RelativeLayout;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.cardview.widget.CardView;

import com.example.cookpro.R;


import java.util.ArrayList;


public class CalendarAdapter extends ArrayAdapter<String> {

    private final LayoutInflater layoutInflater;
    private Context mContext;
    private int layoutResource;
    private ArrayList<String> mArrayList;
    private float cornerRadius = 40;
    private float[] rightBottomRadii = {0,0,0,0,cornerRadius,cornerRadius,0,0};
    private float[] leftBottomRadii = {0,0,0,0,0,0,cornerRadius,cornerRadius};
    private int borderThickness = 1;


    public CalendarAdapter(@NonNull Context context, int layoutResource,  @NonNull ArrayList<String> objects) {
        super(context, layoutResource, objects);

        this.mContext = context;

        this.layoutResource = layoutResource;
        this.mArrayList = objects;
        this.layoutInflater = (LayoutInflater) mContext.getSystemService(Context.LAYOUT_INFLATER_SERVICE);




    }



    private static class ViewHolder{
        CardView cardView;
        TextView Date;
        RelativeLayout relativeLayout;
        GradientDrawable cardDrawable;
        GradientDrawable relDrawable;
    }

    public View getView(int position, View convertView, ViewGroup parent){

        /*Convert View build pattern
         *
         * */
        final ViewHolder viewHolder;

        if(convertView==null){
            convertView = layoutInflater.inflate(layoutResource,parent,false);
            viewHolder = new ViewHolder();
            viewHolder.cardView = convertView.findViewById(R.id.home_card_view_calendar);
            viewHolder.Date = convertView.findViewById(R.id.home_central_date);
            viewHolder.relativeLayout = convertView.findViewById(R.id.home_calendar_date_relview);
            viewHolder.cardDrawable = new GradientDrawable();
            viewHolder.relDrawable = new GradientDrawable();
            convertView.setTag(viewHolder);
        }

        else{
            viewHolder = (ViewHolder) convertView.getTag();
        }

        String date = getItem(position);

        String [] dateCom = date.split("/");
        String dateNum = dateCom[2];
        String presentMonthClassifier = dateCom[3];
        String activeDateClassifier = dateCom[4];

        viewHolder.relDrawable.setShape(GradientDrawable.RECTANGLE);
        viewHolder.cardDrawable.setShape(GradientDrawable.RECTANGLE);
        viewHolder.relDrawable.setStroke(borderThickness,getContext().getResources().getColor(R.color.colorPrimaryDark));

        if(position == mArrayList.size()-7){
            viewHolder.relDrawable.setCornerRadii(leftBottomRadii);
            viewHolder.cardDrawable.setColor(getContext().getResources().getColor(R.color.colorPrimaryDark));

        }

        else if(position == mArrayList.size()-1){
            viewHolder.relDrawable.setCornerRadii(rightBottomRadii);
            viewHolder.cardDrawable.setColor(getContext().getResources().getColor(R.color.colorPrimaryDark));


        }



        if(presentMonthClassifier.equals("Y")){
            viewHolder.relDrawable.setColor(getContext().getResources().getColor(R.color.white));
            viewHolder.Date.setTextColor(getContext().getResources().getColor(R.color.colorPrimaryDark));


        }
        else if(presentMonthClassifier.equals("N")){
            viewHolder.relDrawable.setColor(getContext().getResources().getColor(R.color.colorPrimary));
        }



        if(activeDateClassifier.equals("Y")){
            viewHolder.relDrawable.setColor(getContext().getResources().getColor(R.color.green_active));
            viewHolder.Date.setTextColor(getContext().getResources().getColor(R.color.white));
        }

        viewHolder.relativeLayout.setBackground(viewHolder.relDrawable);
        viewHolder.cardView.setBackground(viewHolder.cardDrawable);

        viewHolder.Date.setText(dateNum);

        return convertView;
    }
}

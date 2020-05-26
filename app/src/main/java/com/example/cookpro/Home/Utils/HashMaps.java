package com.example.cookpro.Home.Utils;

import java.util.HashMap;

public class HashMaps {
    private HashMap<Integer,String> months;
    private HashMap<Integer,String> weekDays;
    public void setMonths(){
        months = new HashMap<Integer,String>();
        months.put(0,"January");
        months.put(1,"February");
        months.put(2,"March");
        months.put(3,"April");
        months.put(4,"May");
        months.put(5,"June");
        months.put(6,"July");
        months.put(7,"August");
        months.put(8,"September");
        months.put(9,"October");
        months.put(10,"November");
        months.put(11,"December");
    }

    public void setWeekDays(){
        weekDays = new HashMap<Integer,String>();
        weekDays.put(0,"Sunday");
        weekDays.put(1,"Monday");
        weekDays.put(2,"Tuesday");
        weekDays.put(3,"Wednesday");
        weekDays.put(4,"Thursday");
        weekDays.put(5,"Friday");
        weekDays.put(6,"Saturday");
    }
}

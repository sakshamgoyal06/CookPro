package com.example.cookpro.Home.Home;

import java.sql.Time;
import java.time.DayOfWeek;
import java.time.Month;
import java.time.Year;
import java.util.Date;

public class DateTransaction {
    private Date date;
    private DayOfWeek day;
    private Month month;
    private Year year;


    public DateTransaction(Date date) {
        this.date = date;
    }

    public Date getDate() {
        return date;
    }

    public void setDate(Date date) {
        this.date = date;
    }

    public DayOfWeek getDay() {
        return day;
    }

    public void setDay(DayOfWeek day) {
        this.day = day;
    }

    public Month getMonth() {
        return month;
    }

    public void setMonth(Month month) {
        this.month = month;
    }

    public Year getYear() {
        return year;
    }

    public void setYear(Year year) {
        this.year = year;
    }
}

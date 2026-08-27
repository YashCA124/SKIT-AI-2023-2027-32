const mongoose = require("mongoose");

const bookingSchema = new mongoose.Schema(
  {
    user: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true,
      index: true,
    },

    parkingLot: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "ParkingLot",
      required: true,
      index: true,
    },

    parkingSlot: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "ParkingSlot",
      required: true,
    },

    vehicleType: {
      type: String,
      enum: ["car", "bike", "suv", "ev"],
      required: true,
    },

    startTime: {
      type: Date,
      required: true,
    },

    endTime: {
      type: Date,
      required: true,
    },

    bookingTime: {
      type: Date,
      default: Date.now,
    },

    durationHours: {
      type: Number,
      required: true,
      min: 0,
    },

    amount: {
      type: Number,
      required: true,
      min: 0,
    },

    status: {
      type: String,
      enum: [
        "confirmed",
        "active",
        "completed",
        "cancelled",
        "no_show",
      ],
      default: "confirmed",
      index: true,
    },

    paymentStatus: {
      type: String,
      enum: ["pending", "paid", "refunded", "failed"],
      default: "pending",
    },

    paymentMethod: {
      type: String,
      enum: ["cash", "upi", "card", "wallet"],
    },

    cancellationTime: {
      type: Date,
    },

    cancellationReason: {
      type: String,
    },
  },
  {
    timestamps: true,
  }
);

// Important for ML queries
bookingSchema.index({
  parkingLot: 1,
  startTime: 1,
});

bookingSchema.index({
  user: 1,
  startTime: -1,
});

bookingSchema.index({
  status: 1,
  startTime: 1,
});

module.exports = mongoose.model("Booking", bookingSchema);